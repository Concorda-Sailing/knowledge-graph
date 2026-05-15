"""Top-level kg CLI dispatcher.

Groups under `kg`:
  project    — registry + per-project config (kg.cli.project)
  depgraph   — code-graph operations (kg.cli.depgraph, subprocess shim Phase 1)
  logigraph  — rules-graph operations (kg.cli.logigraph, subprocess shim Phase 1)
  install    — machine setup (kg.cli.install, subprocess shim Phase 1)
  hook       — Claude Code hook dispatcher (kg.cli.orchestrator)

Top-level back-compat aliases (kg list / add / remove) delegate into
kg.cli.orchestrator so the legacy surface keeps working.
"""
from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="kg",
        description="Knowledge-graph orchestrator and lifecycle CLI.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    from kg.cli import orchestrator, project, depgraph, logigraph, install
    project.register(sub)
    depgraph.register(sub)
    logigraph.register(sub)
    install.register(sub)
    orchestrator.register_alias(sub)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)
    # Subprocess shims (depgraph/logigraph/install) need raw argv to forward;
    # they stash a `wants_extra=True` default via their register() function.
    if getattr(args, "wants_extra", False):
        return args.func(args, extra)
    if extra:
        parser.error(f"unrecognized arguments: {' '.join(extra)}")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
