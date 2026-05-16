"""kg install init — Python port of install.sh's cmd_init().

Scaffolds a fresh project's knowledge-graph data layout:
  <project>/knowledge-graph/
    project.toml
    depgraph/
      project.toml
      extractors/README.md
      nodes/
      dossiers/
      telemetry/
    logigraph/
      project.toml
      CANDIDATES.md
      nodes/rules/
      nodes/domain/
      dossiers/rules/
      dossiers/domain/
      telemetry/

Matches install.sh:cmd_init() byte-for-byte (using the Phase-1
[repos.<key>] sub-table fix in the depgraph project.toml template).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kg.cli.install._shared import color_yellow, err, log, ok

BUNDLE_DIR = "knowledge-graph"
DEFAULT_TARGET = Path.home() / "tools"


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a fresh project data layout. Mirrors install.sh:cmd_init()."""
    project_dir = Path(args.path).expanduser()
    if not project_dir.is_absolute():
        project_dir = Path.cwd() / project_dir
    project_dir = project_dir.resolve()

    bundle = project_dir / BUNDLE_DIR

    if (bundle / "depgraph").exists():
        err(f"{bundle}/depgraph already exists; refusing to overwrite")
        return 1

    log(f"scaffolding project at {color_yellow(str(bundle))}")
    pname = project_dir.name

    # Root project.toml
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "project.toml").write_text(
        f"# Root project descriptor read by `kg` (the orchestrator). Per-subsystem\n"
        f"# configuration lives in depgraph/project.toml and logigraph/project.toml.\n"
        f"\n"
        f"[project]\n"
        f'name = "{pname}"\n'
        f'subsystems = ["depgraph", "logigraph"]\n'
    )

    # depgraph directories
    (bundle / "depgraph" / "extractors").mkdir(parents=True, exist_ok=True)
    (bundle / "depgraph" / "nodes").mkdir(parents=True, exist_ok=True)
    (bundle / "depgraph" / "dossiers").mkdir(parents=True, exist_ok=True)
    (bundle / "depgraph" / "telemetry").mkdir(parents=True, exist_ok=True)

    # depgraph/project.toml
    (bundle / "depgraph" / "project.toml").write_text(
        f"# {pname} depgraph project config.\n"
        f"\n"
        f"[project]\n"
        f'name = "{pname}"\n'
        f"\n"
        f"# Repos this depgraph corpus extracts from. One [repos.<key>] table per\n"
        f"# repo. The key is the logical name extractors reference (e.g. \"api\");\n"
        f"# canonical node ids look like <key>::<rel-path>::<symbol>.\n"
        f"#\n"
        f"# Add a repo with: depgraph repo-add <key> <path> [--extractor ...] [--detector ...]\n"
        f"# List repos with:  depgraph repo-list\n"
        f"#\n"
        f"# [repos.api]\n"
        f'# path = "~/{pname}-api"\n'
        f'# extractor = ["python3", "{{kg_dir}}/depgraph/extractors/generic/python/extract.py"]\n'
        f'# detectors = ["fastapi", "sqlalchemy"]\n'
    )

    # depgraph/extractors/README.md
    (bundle / "depgraph" / "extractors" / "README.md").write_text(
        f"# Extractors\n"
        f"\n"
        f"Drop your extractor scripts in here. Each extractor walks a repo (declared\n"
        f"in `../project.toml [repos]`) and emits JSON node files under `../nodes/`\n"
        f"following the framework schema at `~/tools/{BUNDLE_DIR}/depgraph/schema/node.schema.json`.\n"
        f"\n"
        f"The Concorda reference implementation lives at\n"
        f"`Concorda-Sailing/concorda-depgraph` — clone it for examples:\n"
        f"\n"
        f"- `extract_api.py` — FastAPI route handlers + SQLAlchemy models\n"
        f"- `extract_web.ts` — Next.js components + React hooks\n"
        f"- `extract_tests.ts` — Playwright specs\n"
    )

    # logigraph directories
    (bundle / "logigraph" / "nodes" / "rules").mkdir(parents=True, exist_ok=True)
    (bundle / "logigraph" / "nodes" / "domain").mkdir(parents=True, exist_ok=True)
    (bundle / "logigraph" / "dossiers" / "rules").mkdir(parents=True, exist_ok=True)
    (bundle / "logigraph" / "dossiers" / "domain").mkdir(parents=True, exist_ok=True)
    (bundle / "logigraph" / "telemetry").mkdir(parents=True, exist_ok=True)

    # logigraph/project.toml
    (bundle / "logigraph" / "project.toml").write_text(
        f"# {pname} logigraph project config.\n"
        f"\n"
        f"[project]\n"
        f'name = "{pname}"\n'
        f"\n"
        f"# Path to this project's depgraph data dir.\n"
        f"[depgraph]\n"
        f'data_dir = "{bundle}/depgraph"\n'
    )

    # logigraph/CANDIDATES.md
    (bundle / "logigraph" / "CANDIDATES.md").write_text(
        "# Rule candidates\n"
        "\n"
        "This file is the human notebook for rules that should be authored. Add\n"
        "candidates as you discover them; mark as authored after `bin/logigraph\n"
        "rule-stub` materializes them.\n"
        "\n"
        "### rule::category::short_name\n"
        "- statement: one-sentence rule\n"
        "- why: motivation + history\n"
        "- surfaces: file:line refs\n"
        "- confidence: high | medium | low\n"
    )

    ok(f"scaffolded {bundle}")
    print()
    kg_bin = f"{DEFAULT_TARGET}/{BUNDLE_DIR}/bin/kg"
    print(
        f"{color_yellow('Next:')}\n"
        f"\n"
        f"  Register this graph with the kg orchestrator:\n"
        f"    {kg_bin} add {bundle}\n"
        f"\n"
        f"  Apply the project-agnostic Claude Code hook block (one-time per machine):\n"
        f"    install.sh hooks --apply\n"
        f"\n"
        f"  Or print the hook snippet to merge by hand:\n"
        f"    install.sh hooks"
    )

    return 0
