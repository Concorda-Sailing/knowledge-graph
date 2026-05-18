"""depgraph self-check subcommand handler.

Smoke-tests the hook/extractor pipeline by emitting a fake PreToolUse
payload and asserting the hook produces something.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from depgraph.lib.config import project_repos  # noqa: E402

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
    # The hook subprocess resolves the data dir via $DEPGRAPH_DATA_DIR (or a cwd
    # walk). Neither is reliable here: parent's cwd doesn't have to be the data
    # dir, and the env var isn't set when the CLI was invoked via `kg depgraph
    # --project <name>`. Forward the resolved data dir explicitly.
    proc = subprocess.run(
        ["python3", str(ctx.tool_root / "hooks" / "pre_edit_inject.py")],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
        env={**os.environ, "DEPGRAPH_DATA_DIR": str(ctx.DEPGRAPH)},
    )
    print("hook stdout:")
    print(proc.stdout)
    if proc.returncode != 0:
        # stderr was being silently dropped — that turned every failure into a
        # bare "FAILED rc=1" with no clue why. Surface it.
        print(f"FAILED rc={proc.returncode}", file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        return 1
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("self-check")
    p.set_defaults(func=cmd_self_check)
