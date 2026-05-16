"""Per-invocation context shared by every logigraph subcommand handler.

Eliminates the import-time LOGIGRAPH = resolve_data_dir() side effect
and provides the linked depgraph_dir lookup (logigraph claims against
a depgraph corpus).
"""
from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


_TOOL_ROOT = Path(__file__).resolve().parents[2]
_DEPGRAPH_VENV = _TOOL_ROOT.parent / "depgraph" / ".venv" / "bin" / "python3"
_FRAMEWORK_PYTHON = str(_DEPGRAPH_VENV) if _DEPGRAPH_VENV.exists() else "python3"


def _resolve_depgraph_dir(logigraph_dir: Path) -> Path:
    """Logigraph claims against a depgraph corpus. Source priority:
       1. DEPGRAPH_DATA_DIR env var
       2. [depgraph].data_dir in logigraph's project.toml
       3. SystemExit.
    """
    env = os.environ.get("DEPGRAPH_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    cfg_path = logigraph_dir / "project.toml"
    if cfg_path.exists():
        cfg = tomllib.loads(cfg_path.read_text())
        dg = (cfg.get("depgraph") or {}).get("data_dir")
        if dg:
            return Path(dg).expanduser().resolve()
    raise SystemExit(
        "depgraph data dir not found. Set DEPGRAPH_DATA_DIR or add\n"
        f'[depgraph]\ndata_dir = "..."\nto {cfg_path}'
    )


@dataclass(frozen=True)
class Context:
    """Per-invocation paths derived from the resolved logigraph data dir."""
    LOGIGRAPH: Path
    NODES: Path
    DOSSIERS_DIR: Path
    CALIBRATION_DIR: Path
    TELEMETRY_DIR: Path
    depgraph_dir: Path
    framework_python: str
    tool_root: Path

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> "Context":
        dd = Path(data_dir).expanduser().resolve()
        return cls(
            LOGIGRAPH=dd,
            NODES=dd / "nodes",
            DOSSIERS_DIR=dd / "dossiers",
            CALIBRATION_DIR=dd / "calibration",
            TELEMETRY_DIR=dd / "telemetry",
            depgraph_dir=_resolve_depgraph_dir(dd),
            framework_python=_FRAMEWORK_PYTHON,
            tool_root=_TOOL_ROOT,
        )
