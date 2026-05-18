"""SQLAlchemy plugin.

Activates when `sqlalchemy` is a Python dependency. Contributes the ORM
base-class cues that drive the `model` classifier. Both the 2.x
`DeclarativeBase` form and the legacy `Base` / `BaseModel` aliases are
covered — projects routinely subclass one and re-export it as the other.
"""
from depgraph.lib.classification.config import LanguageCues
from kg.shared.plugins import Plugin, has_pypi_dep

PLUGIN = Plugin(
    name="sqlalchemy",
    detect=lambda repo_path: has_pypi_dep(repo_path, "sqlalchemy"),
    target_versions={"sqlalchemy": "2.0"},
    cues={
        "python": LanguageCues(
            orm_base_classes={
                "DeclarativeBase",  # SQLAlchemy 2.x preferred form
                "Base",             # Legacy alias projects commonly re-export
                "BaseModel",        # Some projects' chosen alias
            },
        ),
    },
)
