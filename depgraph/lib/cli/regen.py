"""depgraph regen — run extractors per [repos.*] then reconcile."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from depgraph.lib.config import project_repos, render_extractor, repo_detectors  # noqa: E402

from ._shared import mark_regen_in_progress
from .context import Context


def cmd_regen(args: argparse.Namespace, ctx: Context) -> int:
    """Run each [repos.<key>].extractor from project.toml, then reconcile."""
    mark_regen_in_progress(ctx)
    env = {**os.environ, "DEPGRAPH_DATA_DIR": str(ctx.DEPGRAPH)}
    failed: list[str] = []
    for key, info in project_repos(ctx.DEPGRAPH).items():
        cmd = render_extractor(info, ctx.DEPGRAPH)
        if cmd is None:
            print(f"--- {key} (no extractor configured; skipping)")
            continue
        cmd += [
            "--repo-key", key,
            "--repo-path", str(info["path"]),
            "--data-dir", str(ctx.DEPGRAPH),
        ]
        detectors = repo_detectors(info)
        if detectors:
            cmd += ["--detectors", ",".join(detectors)]
        cmd += ["--detector-path", str(ctx.DEPGRAPH / "extractors" / "detectors")]
        print(f"--- {key}")
        rc = subprocess.call(cmd, env=env)
        if rc != 0:
            failed.append(key)
    print("--- reconcile")
    rc = subprocess.call(
        [ctx.framework_python, str(ctx.tool_root / "extractors" / "reconcile.py")],
        env=env,
    )
    if rc != 0:
        failed.append("reconcile")
    if failed:
        print(f"\nFAILED stages: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("regen")
    p.add_argument("--all", action="store_true")
    p.add_argument("--since")
    p.set_defaults(func=cmd_regen)
