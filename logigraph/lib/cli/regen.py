"""logigraph regen subcommand — runs the extractor + reconcile pipeline."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from .context import Context


def _mark_regen_in_progress(ctx: Context) -> None:
    """Atomic marker: if regen crashes mid-run, this stays as in_progress
    and the hook surfaces a banner. reconcile.py flips it to complete on
    success."""
    import datetime as _dt

    corpus_meta = ctx.NODES / "_meta.json"
    ctx.NODES.mkdir(parents=True, exist_ok=True)
    payload: dict = {
        "schema_version": 1,
        "regen_status": "in_progress",
        "started_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }
    if corpus_meta.exists():
        try:
            existing = json.loads(corpus_meta.read_text())
            payload = {**existing, **payload}
        except (OSError, json.JSONDecodeError):
            pass
    tmp = corpus_meta.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    tmp.replace(corpus_meta)


def cmd_regen(args: argparse.Namespace, ctx: Context) -> int:
    """Inject LOGIGRAPH_DATA_DIR into the subprocess env so reconcile targets
    the resolved data dir even when the user invoked regen via cwd discovery
    rather than an explicit env var. Mirrors the same fix in depgraph; cheap
    insurance for the day logigraph grows project-owned extractors with their
    own path defaults."""
    _mark_regen_in_progress(ctx)
    from kg.shared.env import LOGIGRAPH_DATA_DIR
    env = {**os.environ, LOGIGRAPH_DATA_DIR: str(ctx.LOGIGRAPH)}
    rc = subprocess.call(
        [ctx.framework_python, str(ctx.tool_root / "extractors" / "reconcile.py")],
        env=env,
    )
    return 0 if rc == 0 else 1


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("regen")
    p.set_defaults(func=cmd_regen)
