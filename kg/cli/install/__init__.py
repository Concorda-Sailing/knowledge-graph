"""kg install — subprocess shim into install.sh.

Phase 1: forwards argv to install.sh (which lives next to the kg/
package). install.sh handles --project / --apply / --target itself,
so kg.cli.install does no project resolution — it's a transparent
wrapper that unifies the help surface.

Phase 4 ports install.sh's logic to Python under this module.
Subcommands with native Python handlers are dispatched directly;
everything else still subprocesses into install.sh (replaced P4T3-P4T8).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from kg.cli.install import bootstrap as _bootstrap_mod
from kg.cli.install import cascade as _cascade_mod
from kg.cli.install import hooks as _hooks_mod
from kg.cli.install import init as _init_mod
from kg.cli.install import path as _path_mod
from kg.cli.install import systemd as _systemd_mod
from kg.cli.install import tools as _tools_mod


def _run_installer(args: argparse.Namespace, extra: list[str]) -> int:
    # Subcommands that have native Python handlers dispatch directly.
    if extra and extra[0] == "init":
        init_parser = argparse.ArgumentParser(
            prog="kg install init",
            description=(
                "Scaffold a fresh project's knowledge-graph data layout. "
                "Supports both data-dir conventions: pass "
                "~/<project>-knowledge-graph for sibling-with-hyphen "
                "(the path is the bundle), or ~/<project> for nested "
                "(the bundle becomes <project>/knowledge-graph/)."
            ),
        )
        init_parser.add_argument(
            "path",
            metavar="DATA_DIR",
            help=(
                "Path to the data directory (sibling-with-hyphen "
                "<project>-knowledge-graph) or the parent dir for the "
                "nested <project>/knowledge-graph layout."
            ),
        )
        init_args = init_parser.parse_args(extra[1:])
        return _init_mod.cmd_init(init_args)
    if extra and extra[0] in ("tools", "install"):
        tools_parser = argparse.ArgumentParser(prog="kg install tools")
        tools_parser.add_argument("--target", default=str(Path.home() / "tools"))
        tools_parser.add_argument("--data", action="append", default=[])
        tools_args = tools_parser.parse_args(extra[1:])
        return _tools_mod.cmd_tools(tools_args)
    if extra and extra[0] == "hooks":
        hooks_parser = argparse.ArgumentParser(prog="kg install hooks")
        hooks_parser.add_argument("--project", help="Project data dir (used in hook command paths)")
        hooks_parser.add_argument("--apply", action="store_true")
        hooks_parser.add_argument("--force", action="store_true")
        return _hooks_mod.cmd_hooks(hooks_parser.parse_args(extra[1:]))
    if extra and extra[0] == "systemd":
        sysd_parser = argparse.ArgumentParser(prog="kg install systemd")
        sysd_parser.add_argument("--target", default=str(Path.home() / "tools"))
        sysd_parser.add_argument("--project")
        sysd_parser.add_argument("--depgraph-data-dir", dest="depgraph_data_dir")
        sysd_parser.add_argument("--logigraph-data-dir", dest="logigraph_data_dir")
        sysd_parser.add_argument("--apply", action="store_true")
        return _systemd_mod.cmd_systemd(sysd_parser.parse_args(extra[1:]))
    if extra and extra[0] == "path":
        path_parser = argparse.ArgumentParser(prog="kg install path")
        path_parser.add_argument("--target", default=str(Path.home() / "tools"))
        path_parser.add_argument("--rcfile", default=None)
        path_parser.add_argument("--apply", action="store_true")
        path_parser.add_argument("--force", action="store_true")
        return _path_mod.cmd_path(path_parser.parse_args(extra[1:]))
    if extra and extra[0] == "bootstrap":
        boot_parser = argparse.ArgumentParser(
            prog="kg install bootstrap",
            description=(
                "One-shot setup: install tools, scaffold the project's "
                "knowledge-graph data dir, write Claude Code hooks, register "
                "with the kg orchestrator, install the graphui systemd unit, "
                "and write the framework's bin dirs into ~/.profile."
            ),
        )
        boot_parser.add_argument(
            "project",
            metavar="DATA_DIR",
            help=(
                "Path to the project's data directory. Either the "
                "sibling-with-hyphen form ~/<project>-knowledge-graph "
                "(used as the bundle directly) or the nested form "
                "~/<project> (becomes <project>/knowledge-graph/)."
            ),
        )
        boot_parser.add_argument(
            "--data", action="append", default=[],
            help="Extra tool data spec passed through to `kg install tools`.",
        )
        return _bootstrap_mod.cmd_bootstrap(boot_parser.parse_args(extra[1:]))
    if extra and extra[0] == "cascade":
        casc_parser = argparse.ArgumentParser(prog="kg install cascade")
        casc_parser.add_argument("target_repo")
        casc_parser.add_argument("--depgraph", default="")
        casc_parser.add_argument("--logigraph", default="")
        casc_parser.add_argument("--apply", action="store_true")
        casc_parser.add_argument("--force", action="store_true")
        return _cascade_mod.cmd_cascade(casc_parser.parse_args(extra[1:]))
    # All subcommands have native handlers as of P4T9; print usage for
    # unknown/missing subcommands. (Falling through to install.sh would
    # recurse infinitely now that install.sh just execs `kg install`.)
    import sys
    if extra and extra[0] in ("-h", "--help"):
        _print_install_help()
        return 0
    if not extra:
        _print_install_help()
        return 1
    print(f"kg install: unknown subcommand {extra[0]!r}", file=sys.stderr)
    print("known subcommands: tools / init / hooks / systemd / path / cascade / bootstrap", file=sys.stderr)
    return 1


def _print_install_help() -> None:
    print(
        "usage: kg install <subcommand> [options]\n"
        "\n"
        "Subcommands:\n"
        "  tools     [--target ... --data ...]              Install/upgrade framework binaries\n"
        "  init      <data-dir>                             Scaffold a fresh project layout\n"
        "  hooks     [--project <dir>] [--apply] [--force]  Write Claude Code hook block to settings.json\n"
        "  systemd   [--project <dir>] [--apply]            Generate + apply graphui systemd unit\n"
        "            [--depgraph-data-dir <p>] [--logigraph-data-dir <p>]\n"
        "  path      [--rcfile ...] [--apply] [--force]     Add framework bin dirs to shell PATH\n"
        "  cascade   <repo> [--depgraph ... --logigraph ...] [--apply] [--force]\n"
        "                                                   Install pre-push hook in a target repo\n"
        "  bootstrap <data-dir> [--data ...]                One-shot: tools + init + hooks + systemd + path\n"
    )


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "install",
        help="Machine setup: tools, hooks, systemd, PATH, cascade, bootstrap.",
        add_help=False,
    )
    p.set_defaults(func=_run_installer, wants_extra=True)
