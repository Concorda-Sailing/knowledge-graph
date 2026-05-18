"""TypeScript / JavaScript language baseline — always active, no
framework-specific cues."""
from depgraph.lib.classification.config import LanguageCues
from kg.shared.plugins import Plugin

PLUGIN = Plugin(
    name="general:typescript",
    detect=lambda _path: True,
    cues={
        "typescript": LanguageCues(
            orm_schema_link_vias={"__tablename__"},
        ),
    },
)
