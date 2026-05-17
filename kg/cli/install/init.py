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
        f"# Required: `path`. Everything else is optional but each toggle below\n"
        f"# changes what ends up in the corpus, so review them when adding a repo.\n"
        f"#\n"
        f"# REQUIRED CONFIGURATION when adding a repo:\n"
        f"#   - path: filesystem location of the checkout.\n"
        f"#   - include_paths / exclude_paths: SCOPE THE CORPUS. The extractors\n"
        f"#     only skip hardcoded build dirs (node_modules, .venv, __pycache__,\n"
        f"#     dist, .git) — they do NOT guess which other trees you want\n"
        f"#     extracted. Almost every real repo needs exclude_paths to drop\n"
        f"#     test directories, generated code, vendored deps, fixture trees,\n"
        f"#     etc. Skipping this step bloats the corpus and produces orphan\n"
        f"#     edges from test files importing things they shouldn't be tracked\n"
        f"#     against. Globs use gitignore-flavoured `**/` semantics and are\n"
        f"#     matched against the file's path relative to `path`.\n"
        f"#\n"
        f"# Optional v2 keys:\n"
        f"#   - languages: any of \"python\", \"typescript\", \"sql\". Inferred from\n"
        f"#     file extensions if omitted.\n"
        f"#   - migrations_dirs: subdirs (relative to `path`) the SQL pipeline\n"
        f"#     scans for migration files. Required if languages includes \"sql\".\n"
        f"#\n"
        f"# Example — replace with your repo(s):\n"
        f"#\n"
        f"# [repos.api]\n"
        f'# path = "~/{pname}-api"\n'
        f'# languages = ["python", "sql"]\n'
        f'# migrations_dirs = ["migrations"]\n'
        f'# exclude_paths = [\n'
        f'#   "**/tests/**",\n'
        f'#   "**/test_*.py",\n'
        f'#   "**/*_test.py",\n'
        f'#   "**/migrations/versions/**",  # if alembic, generated\n'
        f'# ]\n'
        f"#\n"
        f"# [repos.web]\n"
        f'# path = "~/{pname}-web"\n'
        f'# languages = ["typescript"]\n'
        f'# exclude_paths = [\n'
        f'#   "**/__tests__/**",\n'
        f'#   "**/*.test.ts",\n'
        f'#   "**/*.test.tsx",\n'
        f'#   "**/*.spec.ts",\n'
        f'#   "**/build/**",\n'
        f'#   "**/.next/**",\n'
        f'# ]\n'
    )

    # depgraph/extractors/README.md
    (bundle / "depgraph" / "extractors" / "README.md").write_text(
        f"# Extractors\n"
        f"\n"
        f"The shipped per-language extractors at\n"
        f"`~/tools/{BUNDLE_DIR}/depgraph/extractors/{{python,typescript,sql}}/`\n"
        f"are driven by `../project.toml [repos.<key>] languages = [...]`. Most\n"
        f"projects don't need to add anything here — the framework extractors\n"
        f"handle Python, TypeScript/JavaScript, and SQL migrations out of the\n"
        f"box.\n"
        f"\n"
        f"Drop a project-local extractor script in here only if your repo uses\n"
        f"a language the framework doesn't ship. Each extractor walks a repo and\n"
        f"emits JSON node files under `../nodes/` following the framework schema\n"
        f"at `~/tools/{BUNDLE_DIR}/depgraph/schema/node.schema.json`.\n"
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
