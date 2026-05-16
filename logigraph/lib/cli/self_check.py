"""logigraph self-check subcommand — smoke-tests the hook pipeline."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_SELF_CHECK_LIB = Path(__file__).resolve().parents[1]
if str(_SELF_CHECK_LIB) not in sys.path:
    sys.path.insert(0, str(_SELF_CHECK_LIB))
from logigraph.lib.config import project_repos  # noqa: E402

from .context import Context


def cmd_self_check(args: argparse.Namespace, ctx: Context) -> int:
    """Smoke-test the PreToolUse hook end-to-end.

    The hook is intentionally silent for files with no claiming rules, so
    a synthetic path verifies almost nothing. Prefer the first real path
    from the by_file index — that exercises the injection pipeline and
    proves the hook produces non-empty output. Fall back to a synthetic
    path only when the index is empty (early bootstrap), and report that
    case honestly rather than as a green pass."""
    repos = project_repos(ctx.LOGIGRAPH)
    if not repos:
        print("self-check: no [repos.*] configured in project.toml", file=sys.stderr)
        return 1

    sample_path: Path | None = None
    by_file_path = ctx.NODES / "_index" / "by_file.json"
    if by_file_path.exists():
        try:
            idx = json.loads(by_file_path.read_text())
        except (OSError, json.JSONDecodeError):
            idx = {}
        if idx.get("schema_version") == 1:
            basename_to_path = {r["path"].name: r["path"] for r in repos.values()}
            for key, rule_ids in (idx.get("by_file") or {}).items():
                if not rule_ids:
                    continue
                basename, _, rel = key.partition("/")
                repo_path = basename_to_path.get(basename)
                if repo_path is not None and rel:
                    sample_path = repo_path / rel
                    break

    fallback_used = sample_path is None
    if sample_path is None:
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
    if proc.returncode != 0:
        print(f"FAILED rc={proc.returncode}", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        return 1

    if fallback_used:
        print(f"self-check: index empty or unreadable — used synthetic path {sample_path}")
        print("hook returned rc=0 with no injection (expected for an unmatched path)")
        print("run `bin/logigraph regen` to populate the index, then re-run self-check "
              "to exercise the injection pipeline")
        return 0

    if not proc.stdout.strip():
        print(
            f"FAILED: hook produced empty stdout for indexed path {sample_path}, "
            f"which has claiming rules in by_file.json — injection pipeline is broken",
            file=sys.stderr,
        )
        return 2

    print(f"self-check OK — injection ran for {sample_path}")
    print("hook stdout:")
    print(proc.stdout)
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("self-check")
    p.set_defaults(func=cmd_self_check)
