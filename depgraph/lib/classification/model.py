"""Model classifier — ORM mapper class that observes a schema.

Requires BOTH:
  1. `extends` edge to a known ORM base class (config.orm_base_classes).
     Matched by the last `::` segment of the target id so that fully-qualified
     ids like `external::pypi::sqlalchemy::Base` match on "Base".
  2. `references` edge to a primitive whose kind == "schema" AND whose `via`
     field is in config.orm_schema_link_vias (e.g. "__tablename__").

Classes already classified as `schema` (by the SQL extractor) are skipped —
schema is intrinsic to the source language, not a derived classification.
"""
from __future__ import annotations

KIND = "model"


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    # Collect all schema primitive ids (set by extractor, not engine)
    schema_ids = {p["id"] for p in primitives if p.get("kind") == "schema"}

    decisions = {}
    for p in primitives:
        if p["primitive"] != "class":
            continue
        if p.get("kind") == "schema":
            # Already labeled schema by extractor; classifier must not override
            continue

        extends_orm = False
        orm_base_evidence = None
        schema_ref = None

        for e in by_source.get(p["id"], []):
            if e["kind"] == "extends":
                # Match by the last segment of the target id (strips namespace)
                target_last = e["target"].split("::")[-1]
                if target_last in config.orm_base_classes:
                    extends_orm = True
                    orm_base_evidence = {"base": target_last, "via": e["via"]}
            elif (
                e["kind"] == "references"
                and e["target"] in schema_ids
                and e.get("via") in config.orm_schema_link_vias
            ):
                # Only ORM-mapper style references count. `via` must be an
                # orm_schema_link_via marker (default: "__tablename__"). This
                # prevents type-hint references from turning typed args into models.
                schema_ref = {"schema": e["target"], "via": e["via"]}

        if extends_orm and schema_ref is not None:
            decisions[p["id"]] = {
                "rule": "orm_mapper_with_schema_reference",
                "evidence": [orm_base_evidence, schema_ref],
            }
        # extends_orm without schema_ref: orphan mapper — kind stays None.
        # Graphui can surface these as "classes extending ORM base but unclassified".
    return decisions
