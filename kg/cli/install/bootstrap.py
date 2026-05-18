"""kg install bootstrap — one-shot: install tools + scaffold + hooks + systemd + path."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from ._shared import color_yellow, log, ok, warn
from .hooks import cmd_hooks
from .init import BUNDLE_DIR, cmd_init, resolve_bundle_layout
from .path import cmd_path
from .systemd import cmd_systemd
from .tools import cmd_tools


def cmd_bootstrap(args: argparse.Namespace) -> int:
    """One-shot bootstrap: tools → init (or use-existing) → hooks →
    kg add → systemd → path.

    The user's `project` argument is resolved by `resolve_bundle_layout`
    so both data-dir conventions work:
      sibling-with-hyphen   ~/<project>-knowledge-graph/
      nested                ~/<project>/   (becomes <project>/knowledge-graph/)
    See `kg/cli/install/init.py::resolve_bundle_layout` for the rules.
    """
    bundle, pname = resolve_bundle_layout(Path(args.project))
    log(f"bootstrapping {color_yellow(pname)} → {color_yellow(str(bundle))}")
    print()

    # 1. tools (was cmd_install in install.sh)
    tools_args = argparse.Namespace(
        target=str(Path.home() / "tools"),
        data=args.data or [],
    )
    rc = cmd_tools(tools_args)
    if rc != 0:
        return rc
    print()

    # 2. init — scaffold if the bundle's depgraph/logigraph don't exist yet;
    #    otherwise reuse. Pass quiet=True so init doesn't print a stale
    #    "Next:" hint (bootstrap runs those next steps itself).
    if not (bundle / "depgraph").exists() or not (bundle / "logigraph").exists():
        log(f"scaffolding empty project layout at {bundle}")
        init_args = argparse.Namespace(path=str(args.project), quiet=True)
        rc = cmd_init(init_args)
        if rc != 0:
            return rc
        print()
    else:
        log(f"using existing project data at {bundle}")
        print()

    # 3. hooks — bootstrap implies --force (overwrite any existing hooks block).
    log(f"applying Claude Code hooks → ~/.claude/settings.json")
    hooks_args = argparse.Namespace(project=str(bundle), apply=True, force=True)
    rc = cmd_hooks(hooks_args)
    if rc != 0:
        return rc
    print()

    # 4. register with kg orchestrator via `kg add <bundle>`.
    #    Idempotent — re-running with the same path is a no-op success.
    log("registering project with kg orchestrator")
    tool_root = Path(__file__).resolve().parents[3]
    kg_bin = tool_root / "bin" / "kg"
    r = subprocess.run([str(kg_bin), "add", str(bundle)])
    if r.returncode != 0:
        warn(f"kg add failed; run '{kg_bin} add {bundle}' manually")
    print()

    # 5. systemd unit for graphui.
    log("applying systemd unit for graphui")
    sysd_args = argparse.Namespace(
        target=str(Path.home() / "tools"),
        project=str(bundle),
        depgraph_data_dir=None,
        logigraph_data_dir=None,
        apply=True,
    )
    cmd_systemd(sysd_args)  # don't fail bootstrap if systemd's not available
    print()

    # 6. PATH block — bootstrap implies --force (replace any managed block).
    log("applying PATH block to ~/.profile")
    path_args = argparse.Namespace(rcfile=None, apply=True, force=True)
    cmd_path(path_args)
    print()

    ok(f"bootstrap complete — project {color_yellow(pname)}")

    tool_root_str = str(Path.home() / "tools" / BUNDLE_DIR)
    print(f"""
  Tools:          {tool_root_str}/{{depgraph,logigraph,graphui}}/
  Project data:   {bundle}/{{depgraph,logigraph}}/
  Claude Code hooks:  ~/.claude/settings.json
  Shell PATH:     ~/.profile (run 'source ~/.profile' to pick up depgraph/logigraph)

  Note: Claude Code reads settings.json at session start. Restart any
  open sessions to pick up the new hooks.
""")
    return 0
