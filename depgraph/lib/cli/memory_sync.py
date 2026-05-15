"""depgraph memory-sync subcommand handler.

Mirrors Claude's project memories from ~/.claude/.../memory/ into the
project's configured mirror dir (project.toml [memory] mirror, relative
to $HOME) for version control.

Refuses to mirror files containing plaintext credentials — replaces those
lines with a redacted version that points back at the canonical path.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from config import load_project_config  # noqa: E402

from .context import Context


# Patterns that, if matched, force the line to be replaced with a
# placeholder. Conservative: false positives just mean the user has to
# re-read the canonical file when restoring. The patterns target real
# leakage shapes seen in this repo's memories so far.
_LINE_PATTERNS = [
    # Backtick-quoted passwords ("password `hunter2`")
    re.compile(r"password\s+`[^`]+`", re.IGNORECASE),
    # YAML-style "password: value" (excludes REDACTED/null/unset placeholders)
    re.compile(r"^\s*password:\s*(?!(?:REDACTED|null|unset|\s*$))[^\s].*", re.IGNORECASE),
    # `user` / `value` ... creds — catches "Same `lgreenlee` / `in53cure` creds."
    re.compile(r"`[^`]+`\s*/\s*`[^`]+`.*\b(creds|credentials|login)\b", re.IGNORECASE),
    # Inline "user:pass@host" credential URLs
    re.compile(r"://[^/\s:@]+:[^/\s@]+@", re.IGNORECASE),
    # API key / token / secret literal patterns
    re.compile(r"(api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
    re.compile(r"^-----BEGIN\s+(RSA|OPENSSH|EC|DSA|PRIVATE)"),
    # AWS-style secrets
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


def _redact_line(line: str, src_path: Path, line_no: int) -> str:
    """Preserve the leading bullet / heading marker so the file structure
    stays readable; replace the value portion with a pointer."""
    prefix = ""
    m = re.match(r"^(\s*[-*]\s+(?:\*\*[^*]+\*\*\s*[:.]?\s*)?|\s*#+\s+)", line)
    if m:
        prefix = m.group(1)
    return (
        prefix
        + f"REDACTED — see canonical memory at `{src_path}` (line {line_no})"
    )


def cmd_memory_sync(args: argparse.Namespace, ctx: Context) -> int:
    """Mirror Claude's project memories from ~/.claude/.../memory/ into
    the project's configured mirror dir (project.toml [memory] mirror,
    relative to $HOME) for version control.

    Refuses to mirror files containing plaintext credentials — replaces those
    files with a redacted version that points back at the canonical path.
    """
    # Claude encodes the project name by replacing path separators in $HOME.
    home_encoded = str(Path.home()).replace("/", "-")
    canonical = Path.home() / ".claude" / "projects" / home_encoded / "memory"

    cfg = load_project_config(ctx.DEPGRAPH)
    mirror_rel = (cfg.get("memory") or {}).get("mirror")
    if not mirror_rel:
        print(
            "memory-sync: no [memory] mirror configured in project.toml — nothing to do.",
            file=sys.stderr,
        )
        return 1
    mirror = Path.home() / mirror_rel
    if not canonical.exists():
        print(f"canonical memory dir not found: {canonical}", file=sys.stderr)
        return 1
    mirror.mkdir(parents=True, exist_ok=True)

    written = 0
    redacted_files: list[str] = []
    for src in canonical.glob("*.md"):
        text = src.read_text()
        original_lines = text.splitlines(keepends=False)
        had_match = False
        rebuilt: list[str] = []
        for line_no, line in enumerate(original_lines, 1):
            matched = any(pat.search(line) for pat in _LINE_PATTERNS)
            if matched:
                had_match = True
                rebuilt.append(_redact_line(line, src.relative_to(Path.home()), line_no))
            else:
                rebuilt.append(line)
        new_text = "\n".join(rebuilt)
        if text.endswith("\n"):
            new_text += "\n"

        dest = mirror / src.name
        if had_match:
            dest.write_text(new_text)
            redacted_files.append(src.name)
        else:
            dest.write_text(text)
        written += 1

    # Detect deletions: files in mirror but not in canonical
    canonical_names = {f.name for f in canonical.glob("*.md")}
    stale = [f for f in mirror.glob("*.md") if f.name not in canonical_names and f.name != "README.md"]
    for f in stale:
        f.unlink()

    print(f"memory-sync: wrote {written} file(s) to {mirror.relative_to(Path.home())}")
    if redacted_files:
        print(f"redacted: {len(redacted_files)} file(s)")
        for name in redacted_files[:5]:
            print(f"  - {name}")
        if len(redacted_files) > 5:
            print(f"  ... +{len(redacted_files) - 5} more")
    if stale:
        print(f"removed stale (no longer in canonical): {len(stale)}")
        for f in stale[:5]:
            print(f"  - {f.name}")

    # Auto-commit the mirror so memory history is versioned end-to-end.
    # Skip silently if the mirror isn't a git repo (legitimate config).
    if (mirror / ".git").exists():
        status = subprocess.run(
            ["git", "-C", str(mirror), "status", "--porcelain"],
            capture_output=True, text=True,
        )
        if status.returncode != 0:
            print(
                f"memory-sync: git status failed in mirror: {status.stderr.strip()}",
                file=sys.stderr,
            )
        elif status.stdout.strip():
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            msg = f"auto-snapshot {timestamp}"
            add = subprocess.run(
                ["git", "-C", str(mirror), "add", "-A"],
                capture_output=True, text=True,
            )
            if add.returncode != 0:
                print(
                    f"memory-sync: git add failed: {add.stderr.strip()}",
                    file=sys.stderr,
                )
            else:
                commit = subprocess.run(
                    ["git", "-C", str(mirror), "commit", "-m", msg],
                    capture_output=True, text=True,
                )
                if commit.returncode != 0:
                    print(
                        f"memory-sync: git commit failed: {commit.stderr.strip()}",
                        file=sys.stderr,
                    )
                else:
                    print(f"memory-sync: committed {msg}")
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "memory-sync",
        help="Mirror ~/.claude memories into project.toml [memory] mirror dir",
    )
    p.set_defaults(func=cmd_memory_sync)
