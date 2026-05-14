"""Parse a knowledge-graph repo's root ``project.toml``.

A graph repo's layout::

    <graph>/
    ├── project.toml          # name, subsystems, source_roots
    ├── depgraph/
    │   └── project.toml      # subsystem-specific config (extractors, [repos.*])
    └── logigraph/
        └── project.toml

The root ``project.toml`` declares::

    [project]
    name = "..."
    subsystems = ["depgraph", "logigraph"]
    source_roots = ["~/code/foo", "~/code/bar"]   # optional
    tooling_version = "1.2.3"                     # optional

If ``source_roots`` is omitted at the root, ``load()`` falls back to the
union of ``[repos.*].path`` values in ``depgraph/project.toml``. This
avoids duplicating the source-repo list when depgraph already tracks it.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class GraphProject:
    """In-memory representation of a graph repo's project metadata."""

    name: str
    path: Path  # absolute path to the graph repo root
    subsystems: list[str]
    source_roots: list[Path]  # absolute, ~ expanded; existence not enforced
    tooling_version: Optional[str] = None
    raw: dict = field(default_factory=dict)

    def owns(self, file_path: Path | str) -> bool:
        """Return True if ``file_path`` lies under any of this graph's roots."""
        target = Path(file_path).expanduser()
        # Resolve only if it exists; otherwise compare on the un-resolved form
        # so we don't fail on hypothetical paths.
        if target.exists():
            target = target.resolve()
        else:
            target = target.absolute()
        for root in self.source_roots:
            try:
                target.relative_to(root)
                return True
            except ValueError:
                continue
        return False


def _resolve_path(raw: str) -> Path:
    """Expand ``~`` and make absolute, without requiring existence."""
    p = Path(raw).expanduser()
    if p.exists():
        return p.resolve()
    return p.absolute()


def _derive_source_roots_from_depgraph(graph_dir: Path) -> list[Path]:
    """Pull [repos.*].path values from depgraph/project.toml, if present."""
    dep_toml = graph_dir / "depgraph" / "project.toml"
    if not dep_toml.exists():
        return []
    data = tomllib.loads(dep_toml.read_text())
    repos = data.get("repos") or {}
    paths: list[Path] = []
    for repo_cfg in repos.values():
        raw = repo_cfg.get("path")
        if raw:
            paths.append(_resolve_path(raw))
    return paths


def load(graph_dir: Path) -> GraphProject:
    """Read ``<graph_dir>/project.toml`` and return a ``GraphProject``.

    Raises:
        FileNotFoundError: if ``project.toml`` is missing.
        ValueError: if required fields (``name``, ``subsystems``,
            ``source_roots``) cannot be resolved.
    """
    graph_dir = Path(graph_dir).expanduser().resolve()
    toml_path = graph_dir / "project.toml"
    if not toml_path.exists():
        raise FileNotFoundError(f"Missing {toml_path}")

    data = tomllib.loads(toml_path.read_text())
    proj = data.get("project") or {}
    name = proj.get("name")
    if not name:
        raise ValueError(f"{toml_path}: [project].name is required")

    subsystems = proj.get("subsystems")
    if not subsystems:
        raise ValueError(f"{toml_path}: [project].subsystems is required")

    raw_roots = proj.get("source_roots")
    if raw_roots:
        source_roots = [_resolve_path(r) for r in raw_roots]
    else:
        source_roots = _derive_source_roots_from_depgraph(graph_dir)
        if not source_roots:
            raise ValueError(
                f"{toml_path}: source_roots is required either in [project] or "
                f"derivable from depgraph/project.toml [repos.*].path"
            )

    return GraphProject(
        name=name,
        path=graph_dir,
        subsystems=list(subsystems),
        source_roots=source_roots,
        tooling_version=proj.get("tooling_version"),
        raw=data,
    )
