"""Language registry loader. Reads languages.toml from framework + optionally
a per-project `[languages.*]` block in project.toml. Per-project entries
override framework entries by name; entirely-new languages get added."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Language:
    name: str
    extensions: list[str]
    extractor: Path
    runtime: str


def _read_languages_section(toml_path: Path, *, base_dir: Path) -> dict[str, Language]:
    data = tomllib.loads(toml_path.read_text())
    out: dict[str, Language] = {}
    for name, spec in data.get("languages", {}).items():
        out[name] = Language(
            name=name,
            extensions=list(spec["extensions"]),
            extractor=(base_dir / spec["extractor"]).resolve(),
            runtime=spec["runtime"],
        )
    return out


def load_languages(framework_toml: Path,
                    project_toml: Path | None = None) -> list[Language]:
    """Load framework languages, then merge any per-project overrides /
    additions from project_toml's `[languages.*]` section.

    `extractor` paths in framework_toml resolve relative to the framework
    root (parent of `depgraph/`). Paths in project_toml resolve relative
    to project_toml's parent.
    """
    framework_root = framework_toml.parent.parent
    merged = _read_languages_section(framework_toml, base_dir=framework_root)
    if project_toml is not None and project_toml.exists():
        project_root = project_toml.parent
        for name, lang in _read_languages_section(project_toml,
                                                    base_dir=project_root).items():
            merged[name] = lang  # project overrides framework on name collision
    return list(merged.values())
