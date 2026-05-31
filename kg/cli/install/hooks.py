"""kg install hooks — write hook blocks for Claude Code and/or Grok.

The hook commands all point at ``bin/kg hook <phase>`` so the kg orchestrator
handles per-graph dispatch. No project-specific paths are embedded.

Grok natively reads ~/.claude/settings.json (for compatibility) **and**
~/.grok/hooks/*.json. We can therefore provide first-class Grok support by
writing a native hook file when requested.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from kg.hook import HOOK_PHASES

from ._shared import backup_file, log, ok, warn


# ---------------------------------------------------------------------------
# Hook block generators (shared shape, different targets)
# ---------------------------------------------------------------------------


def _hook_block(tool_root: Path) -> dict:
    """Return the hooks dict used for both Claude settings.json and Grok native hooks.

    The structure is the Claude Code shape. Grok accepts it (with tool name
    aliasing for Bash/Edit/Read/etc.) and also understands the
    hookSpecificOutput envelope that kg hook emits for context injection.
    """
    kg = str(tool_root / "bin" / "kg")
    return {
        "PreToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{kg} hook pre-edit",
                        "timeout": 10,
                    }
                ],
            },
            {
                "matcher": "Bash|mcp__.*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{kg} hook pre-irreversible",
                        "timeout": 5,
                    }
                ],
            },
        ],
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{kg} hook post-edit",
                        "timeout": 120,
                    }
                ]
            }
        ],
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{kg} hook session-start",
                        "timeout": 30,
                    }
                ]
            }
        ],
        "SessionEnd": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{kg} hook session-end",
                        "timeout": 30,
                    }
                ]
            }
        ],
    }


# Local lookup so the f-strings below read the phase names from the
# single-source HOOK_PHASES tuple instead of repeating string literals.
# If a phase is renamed in kg/hook.py, this dict's KeyError surfaces the
# missing wiring immediately.
_PHASE = {name: name for name in HOOK_PHASES}


_SETTINGS_REL = Path(".claude") / "settings.json"
_BUNDLE_DIR = "knowledge-graph"


# The canonical _hook_block() implementation lives above (lines ~20-92).
# It is used for both Claude settings.json and native Grok ~/.grok/hooks/ files.
# This stub is intentionally left as a no-op marker to avoid accidental
# re-introduction of the old duplicated definition during edits.


def _flatten(h: dict | None) -> set[tuple[str, str | None, str]]:
    """Flatten a hooks dict into a set of (top_key, matcher_or_None, command) tuples.

    Mirrors the flatten() helper in install.sh's embedded Python snippet.
    The command string captures what we care about preserving (paths, scripts)
    without locking on cosmetic differences like timeout.
    """
    out: set[tuple[str, str | None, str]] = set()
    for top_key, blocks in (h or {}).items():
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            matcher = block.get("matcher")
            for entry in (block.get("hooks") or []):
                out.add((top_key, matcher, entry.get("command", "")))
    return out


def _resolve_targets(args: argparse.Namespace) -> list[str]:
    """Return list of targets from --for value."""
    t = (getattr(args, "targets", "both") or "both").lower()
    if t == "both":
        return ["claude", "grok"]
    if t in ("claude", "grok"):
        return [t]
    return ["claude", "grok"]


def _write_grok_native_hooks(tool_root: Path, apply: bool, force: bool) -> int:
    """Write (or dry-run) a native Grok hook file at ~/.grok/hooks/knowledge-graph.json."""
    block = _hook_block(tool_root)
    hooks_dir = Path(os.environ.get("HOME", str(Path.home()))).expanduser() / ".grok" / "hooks"
    hooks_file = hooks_dir / "knowledge-graph.json"

    if not apply:
        print(json.dumps({"hooks": block}, indent=2))
        # Annotation goes to stderr so stdout stays parseable JSON.
        print(f"# Would write the above to {hooks_file}", file=sys.stderr)
        return 0

    hooks_dir.mkdir(parents=True, exist_ok=True)

    existing_text = hooks_file.read_text() if hooks_file.exists() else ""
    if existing_text.strip():
        try:
            existing: dict = json.loads(existing_text)
        except json.JSONDecodeError:
            backup_file(hooks_file)
            existing = {}
    else:
        existing = {}

    existing_block = existing.get("hooks")

    if existing_block == block:
        ok(f"Grok hooks already match in {hooks_file} — no-op")
        return 0

    # For the native Grok file we are more lenient than Claude settings.json.
    # We still warn on --force, but we allow overwrite of our own keys.
    if existing_block is not None and not force:
        print(
            f"⚠ {hooks_file} already has a 'hooks' section.", file=sys.stderr
        )
        print(
            "  Re-run with '--apply --force' to overwrite, or edit manually.",
            file=sys.stderr,
        )
        return 2

    backup_file(hooks_file)
    existing["hooks"] = block
    hooks_file.write_text(json.dumps(existing, indent=2) + "\n")
    ok(f"wrote Grok native hooks into {hooks_file}")
    return 0


def cmd_hooks(args: argparse.Namespace) -> int:
    """Install knowledge-graph hooks for Claude Code and/or Grok.

    --for both (default)  → writes to ~/.claude/settings.json (read by both)
                            + writes ~/.grok/hooks/knowledge-graph.json (Grok native)
    --for claude          → only the Claude settings.json path
    --for grok            → only the native Grok hooks file
    """
    tool_root = Path(__file__).resolve().parents[3]
    targets = _resolve_targets(args)

    # Dry-run path: show the block once
    if not args.apply:
        block = _hook_block(tool_root)
        print(json.dumps({"hooks": block}, indent=2))
        # Annotation goes to stderr so stdout stays parseable JSON (callers pipe it).
        print(f"# Targets that would be written: {', '.join(targets)}", file=sys.stderr)
        return 0

    overall_rc = 0

    if "claude" in targets:
        # --- Claude / shared settings.json path (Grok also reads this) ---
        settings_path = (
            Path(os.environ.get("HOME", str(Path.home()))).expanduser()
            / ".claude"
            / "settings.json"
        )
        settings_path.parent.mkdir(parents=True, exist_ok=True)

        block = _hook_block(tool_root)

        existing_text = settings_path.read_text() if settings_path.exists() else ""
        if existing_text.strip():
            try:
                settings: dict = json.loads(existing_text)
            except json.JSONDecodeError:
                backup_file(settings_path)
                settings = {}
        else:
            settings = {}

        existing_hooks: dict | None = settings.get("hooks")

        if existing_hooks == block:
            ok(f"hooks already match in {settings_path} — no-op")
        else:
            new_flat = _flatten(block)
            existing_flat = _flatten(existing_hooks)
            extras = sorted(existing_flat - new_flat)

            if extras:
                # Extras are hook entries kg install can't reproduce (e.g. a
                # user's custom hook or an arbitrary old kg path). We never
                # clobber them — not even with --force, since we can't restore
                # what we can't reproduce. The caller must remove them manually.
                print(
                    "⚠ refusing to write: settings.json has hook entries beyond what "
                    "kg install hooks would generate.",
                    file=sys.stderr,
                )
                if args.force:
                    print(
                        "  --force does not clobber these (kg can't reproduce them). "
                        "Remove the extra entries manually, then re-run.",
                        file=sys.stderr,
                    )
                else:
                    print(
                        "  Remove the extra entries manually, then re-run.",
                        file=sys.stderr,
                    )
                overall_rc = 2
            elif existing_hooks is not None and not args.force:
                print(
                    "⚠ settings.json has a different 'hooks' section. "
                    "Re-run with '--apply --force' to overwrite.",
                    file=sys.stderr,
                )
                overall_rc = 2
            else:
                backup_file(settings_path)
                settings["hooks"] = block
                settings_path.write_text(json.dumps(settings, indent=2) + "\n")
                ok(f"wrote hooks into {settings_path}")

    if "grok" in targets:
        rc = _write_grok_native_hooks(tool_root, apply=True, force=args.force)
        if rc != 0:
            overall_rc = rc

    return overall_rc
