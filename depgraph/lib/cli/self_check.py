"""depgraph self-check subcommand handler.

Smoke-tests the hook/extractor pipeline by emitting a fake PreToolUse
payload and asserting the hook produces something.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from config import project_repos  # noqa: E402

from .context import Context


def cmd_self_check(args: argparse.Namespace, ctx: Context) -> int:
    """Smoke-test: emit a fake PreToolUse payload and assert the hook produces something.
    The payload's file_path is synthesized from the first configured [repos.*] table."""
    repos = project_repos(ctx.DEPGRAPH)
    if not repos:
        print("self-check: no [repos.*] configured in project.toml", file=sys.stderr)
        return 1
    first = next(iter(repos.values()))
    sample_path = first["path"] / "self-check-fake.py"
    payload = json.dumps(
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(sample_path)},
        }
    )
    proc = subprocess.run(
        ["python3", str(ctx.tool_root / "hooks" / "pre_edit_inject.py")],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
    )
    print("hook stdout:")
    print(proc.stdout)
    if proc.returncode != 0:
        print(f"FAILED rc={proc.returncode}", file=sys.stderr)
        return 1
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("self-check")
    p.set_defaults(func=cmd_self_check)
