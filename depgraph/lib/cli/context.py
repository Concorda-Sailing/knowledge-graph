"""Per-invocation context shared by every depgraph subcommand handler.

Eliminates the import-time `DEPGRAPH = resolve_data_dir(...)` side effect
that prevented kg.cli.depgraph from importing handlers natively.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# Tool location (where this package lives) — schemas, framework code.
_TOOL_ROOT = Path(__file__).resolve().parents[2]
_VENV_PYTHON = _TOOL_ROOT / ".venv" / "bin" / "python3"
_FRAMEWORK_PYTHON = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else "python3"


@dataclass(frozen=True)
class Context:
    """Per-invocation paths derived from the resolved depgraph data dir.

    Built once in main() and passed to every cmd_* handler.
    """
    DEPGRAPH: Path
    NODES: Path
    DEPENDENTS_INDEX: Path
    CORPUS_META: Path
    TELEMETRY_DIR: Path
    INJECTIONS_LOG: Path
    ACKS_LOG: Path
    framework_python: str
    tool_root: Path

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> "Context":
        dd = Path(data_dir).expanduser().resolve()
        nodes = dd / "nodes"
        return cls(
            DEPGRAPH=dd,
            NODES=nodes,
            DEPENDENTS_INDEX=nodes / "_index" / "dependents.json",
            CORPUS_META=nodes / "_meta.json",
            TELEMETRY_DIR=dd / "telemetry",
            INJECTIONS_LOG=dd / "telemetry" / "injections.jsonl",
            ACKS_LOG=dd / "telemetry" / "acknowledgments.jsonl",
            framework_python=_FRAMEWORK_PYTHON,
            tool_root=_TOOL_ROOT,
        )
