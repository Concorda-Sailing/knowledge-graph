"""kg install hooks — write Claude Code hook block to settings.json.

Mirrors install.sh:cmd_hooks() and generate_hooks_json(). The hook
commands all point at ``bin/kg hook <phase>`` so the kg orchestrator
handles per-graph dispatch — settings.json carries no project-specific
paths.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from kg.hook import HOOK_PHASES

from ._shared import backup_file, log, ok, warn


# Local lookup so the f-strings below read the phase names from the
# single-source HOOK_PHASES tuple instead of repeating string literals.
# If a phase is renamed in kg/hook.py, this dict's KeyError surfaces the
# missing wiring immediately.
_PHASE = {name: name for name in HOOK_PHASES}


_SETTINGS_REL = Path(".claude") / "settings.json"
_BUNDLE_DIR = "knowledge-graph"


def _hook_block(tool_root: Path) -> dict:
    """Return the hooks dict matching install.sh:generate_hooks_json() exactly.

    Structure::

        {
          "PreToolUse": [
            {"matcher": "Edit|Write|MultiEdit", "hooks": [{"type": "command",
              "command": "<kg> hook pre-edit", "timeout": 10}]},
            {"matcher": "Bash|mcp__.*", "hooks": [{"type": "command",
              "command": "<kg> hook pre-irreversible", "timeout": 5}]},
          ],
          "Stop": [{"hooks": [{"type": "command",
              "command": "<kg> hook post-edit", "timeout": 120}]}],
          "SessionStart": [...],
          "SessionEnd": [...],
        }
    """
    kg = str(tool_root / "bin" / "kg")
    return {
        "PreToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{kg} hook {_PHASE['pre-edit']}",
                        "timeout": 10,
                    }
                ],
            },
            {
                "matcher": "Bash|mcp__.*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{kg} hook {_PHASE['pre-irreversible']}",
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
                        "command": f"{kg} hook {_PHASE['post-edit']}",
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
                        "command": f"{kg} hook {_PHASE['session-start']}",
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
                        "command": f"{kg} hook {_PHASE['session-end']}",
                        "timeout": 30,
                    }
                ]
            }
        ],
    }


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


def cmd_hooks(args: argparse.Namespace) -> int:
    """Port of install.sh:cmd_hooks().

    Generates the Claude Code hook block and, with --apply, merges it into
    ~/.claude/settings.json.  Backs up the file before any write.  Refuses
    to clobber hook entries that install.sh could not reproduce (even with
    --force).
    """
    # tool_root is the repository root (parents[3] from kg/cli/install/hooks.py)
    tool_root = Path(__file__).resolve().parents[3]
    block = _hook_block(tool_root)

    if not args.apply:
        # Dry-run: print valid JSON so the user can copy or pipe it.
        print(json.dumps({"hooks": block}, indent=2))
        return 0

    # --apply: idempotent merge into ~/.claude/settings.json
    settings_path = (
        Path(os.environ.get("HOME", str(Path.home()))).expanduser()
        / ".claude"
        / "settings.json"
    )
    settings_path.parent.mkdir(parents=True, exist_ok=True)

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

    # Fast path: already identical — no-op success.
    if existing_hooks == block:
        ok(f"hooks already match in {settings_path} — no-op")
        return 0

    new_flat = _flatten(block)
    existing_flat = _flatten(existing_hooks)
    extras = sorted(existing_flat - new_flat)

    if extras:
        print(
            "⚠ refusing to write: settings.json has hook entries beyond what "
            "install.sh would generate.",
            file=sys.stderr,
        )
        print(
            "  --force will NOT bypass this check; these entries can't be "
            "reproduced from install.sh args.",
            file=sys.stderr,
        )
        print("  Entries that would be lost:", file=sys.stderr)
        for top, matcher, cmd in extras:
            loc = top + (f" / {matcher}" if matcher else "")
            print(f"    [{loc}] {cmd}", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "  To proceed: back up settings.json, remove the conflicting entries "
            "(or the entire 'hooks' key),",
            file=sys.stderr,
        )
        print(
            "  and re-run. Run without --apply to see the snippet install.sh "
            "would write.",
            file=sys.stderr,
        )
        return 2

    if existing_hooks is not None and not args.force:
        print(
            "⚠ settings.json has a different 'hooks' section.", file=sys.stderr
        )
        print(
            f"  Existing keys: {list(existing_hooks.keys())}", file=sys.stderr
        )
        print(
            "  Re-run with '--apply --force' to overwrite, or merge manually",
            file=sys.stderr,
        )
        print(
            "  (run without --apply to see the snippet).", file=sys.stderr
        )
        return 2

    backup_file(settings_path)
    settings["hooks"] = block
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    ok(f"wrote hooks into {settings_path}")
    return 0
