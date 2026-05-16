"""kg install path — generate or apply the shell PATH block.

Mirrors install.sh:generate_path_snippet() and install.sh:cmd_path().

Writes a sentinel-guarded PATH block to a shell rcfile (default ~/.profile)
that adds the depgraph and logigraph bin/ directories to $PATH so interactive
shells and the LLM's Bash tool can resolve the CLIs.

Idempotent. --force required to replace a block pointing at a different target.
Backs up the rcfile before overwrite.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from ._shared import backup_file, die, err, log, ok, warn

# Sentinel that marks the start of the managed block.  Must match install.sh
# exactly — existing installs' rcfiles use this string to locate the block.
PATH_BLOCK_MARKER = (
    "# Knowledge-graph framework CLIs (depgraph, logigraph) — managed by install.sh"
)

_BUNDLE_DIR = "knowledge-graph"
_DEFAULT_TARGET_RELATIVE = "tools"  # $HOME/tools


def _default_target() -> str:
    home = os.environ.get("HOME", str(Path.home()))
    return str(Path(home) / _DEFAULT_TARGET_RELATIVE)


def _default_rcfile() -> str:
    home = os.environ.get("HOME", str(Path.home()))
    return str(Path(home) / ".profile")


def generate_path_snippet(target: str) -> str:
    """Return the PATH block content for *target*.

    Mirrors install.sh:generate_path_snippet() exactly.  The returned string
    ends with a single trailing newline (as the bash heredoc produces).
    """
    bundle = f"{target}/{_BUNDLE_DIR}"
    return (
        f"{PATH_BLOCK_MARKER}\n"
        f'if [ -d "{bundle}/depgraph/bin" ] ; then\n'
        f'    PATH="{bundle}/depgraph/bin:$PATH"\n'
        f"fi\n"
        f'if [ -d "{bundle}/logigraph/bin" ] ; then\n'
        f'    PATH="{bundle}/logigraph/bin:$PATH"\n'
        f"fi\n"
        f"export PATH\n"
    )


def cmd_path(args: argparse.Namespace) -> int:
    """Port of install.sh:cmd_path().

    Without --apply, prints a header comment and the block to stdout.
    With --apply, idempotently merges the block into the rcfile.

    Three cases (mirrors the embedded python3 script in install.sh):
      1. No sentinel present        → append block.
      2. Sentinel present, same target  → no-op.
      3. Sentinel present, different target → require --force; backup + rewrite.
    """
    target: str = getattr(args, "target", None) or _default_target()
    rcfile_arg: str | None = getattr(args, "rcfile", None)
    apply: bool = getattr(args, "apply", False)
    force: bool = getattr(args, "force", False)

    rcfile = rcfile_arg if rcfile_arg else _default_rcfile()

    new_block = generate_path_snippet(target)

    if not apply:
        print(
            f"# Append the following to {rcfile} (or re-run with --apply to write it\n"
            f"# automatically; --apply --force replaces a managed block pointing at a\n"
            f"# different target after backing it up).\n"
        )
        print(new_block, end="")
        return 0

    # --apply path -----------------------------------------------------------

    p = Path(rcfile)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.touch()

    text = p.read_text()
    lines = text.splitlines()

    # Find sentinel line index.
    start: int | None = None
    for i, ln in enumerate(lines):
        if PATH_BLOCK_MARKER in ln:
            start = i
            break

    if start is None:
        # Case 1: no existing block — append.
        sep = "" if text.endswith("\n") or text == "" else "\n"
        p.write_text(text + sep + "\n" + new_block.rstrip() + "\n")
        ok(f"appended PATH block to {rcfile}")
        return 0

    # Find end of block: walk forward over PATH-block-shaped lines.
    end = start + 1
    while end < len(lines):
        ln = lines[end].lstrip()
        if ln.startswith(("if ", "PATH=", "fi", "export PATH", "    PATH=")) or ln == "":
            end += 1
            # Stop one line past `fi` followed by `export PATH` followed by blank
            if (
                lines[end - 1].strip() == ""
                and end >= 2
                and lines[end - 2].strip() == "export PATH"
            ):
                break
        else:
            break

    existing = "\n".join(lines[start:end]).rstrip()
    new_block_stripped = new_block.rstrip()

    if existing == new_block_stripped:
        ok(f"PATH block already current in {rcfile} — no-op")
        return 0

    if not force:
        print(
            f"⚠ {rcfile} has a managed PATH block pointing at a different target.",
            file=sys.stderr,
        )
        next_line = lines[start + 1] if start + 1 < len(lines) else "(empty)"
        print(f"  Existing first line: {next_line}", file=sys.stderr)
        print(
            "  Re-run with '--apply --force' to replace it (a backup will be made).",
            file=sys.stderr,
        )
        return 2

    # Backup before rewrite.
    bak = p.with_suffix(p.suffix + f".bak.{int(time.time())}")
    import shutil
    shutil.copy2(p, bak)
    log(f"backed up to {bak}")

    new_lines = lines[:start] + new_block_stripped.splitlines() + lines[end:]
    p.write_text("\n".join(new_lines).rstrip() + "\n")
    ok(f"rewrote PATH block in {rcfile}")
    return 0
