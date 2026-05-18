"""Python language baseline — always active, no framework-specific cues."""
from depgraph.lib.classification.config import LanguageCues
from depgraph.plugins.base import Plugin

PLUGIN = Plugin(
    name="general:python",
    detect=lambda _path: True,
    cues={
        "python": LanguageCues(
            # The `__tablename__` attribute is a SQLAlchemy convention but
            # also used by enough other ORMs (e.g. some Django patterns, some
            # custom ORMs) that we treat it as a Python-level baseline. The
            # SQLAlchemy plugin can extend with library-specific cues.
            orm_schema_link_vias={"__tablename__"},
        ),
    },
)
