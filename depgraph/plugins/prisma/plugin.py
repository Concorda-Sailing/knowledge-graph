"""Prisma plugin (TypeScript).

Activates when `@prisma/client` is an npm dep or a `prisma/schema.prisma`
marker exists. Contributes the ORM base-class cues for TS projects using
Prisma; once a Prisma DSL extractor lands, this plugin can also contribute
`orm_schema_link_vias` for `@@map` -> tablename resolution.
"""
from depgraph.lib.classification.config import LanguageCues
from kg.shared.plugins import Plugin, has_marker_file, has_npm_dep

PLUGIN = Plugin(
    name="prisma",
    detect=lambda repo_path: (
        has_npm_dep(repo_path, "@prisma/client")
        or has_marker_file(repo_path, "prisma/schema.prisma", "schema.prisma")
    ),
    cues={
        "typescript": LanguageCues(
            orm_base_classes={"Model", "BaseEntity"},
        ),
    },
)
