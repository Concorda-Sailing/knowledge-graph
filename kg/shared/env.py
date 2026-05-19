"""Single source of truth for environment-variable names shared across the
depgraph, logigraph, kg, and graphui subsystems (#64).

Treat these as the canonical spelling. Read sites (`os.environ.get(...)`,
`resolve_data_dir(...)`) and write sites (subprocess `env={...}` dicts,
systemd unit content) import these constants instead of repeating the
literal — so a rename touches one file and the rest follows.

Docstrings and user-facing prose may still spell the variable inline;
the rule is for *code* that reads or sets the env, not for documentation
that names the variable to the reader.
"""
from __future__ import annotations

# Depgraph corpus root (`~/<project>-knowledge-graph/depgraph`).
DEPGRAPH_DATA_DIR = "DEPGRAPH_DATA_DIR"

# Logigraph corpus root (`~/<project>-knowledge-graph/logigraph`).
LOGIGRAPH_DATA_DIR = "LOGIGRAPH_DATA_DIR"

# graphui uses this for the registered-graphs override (kg/cli/resolve.py).
KG_REGISTRY_PATH = "KG_REGISTRY_PATH"

# Internal: set by `depgraph/bin/depgraph` after re-exec into its venv so it
# doesn't recurse. Not user-facing — listed here for completeness.
KG_NO_VENV_REEXEC = "KG_NO_VENV_REEXEC"

__all__ = (
    "DEPGRAPH_DATA_DIR",
    "LOGIGRAPH_DATA_DIR",
    "KG_REGISTRY_PATH",
    "KG_NO_VENV_REEXEC",
)
