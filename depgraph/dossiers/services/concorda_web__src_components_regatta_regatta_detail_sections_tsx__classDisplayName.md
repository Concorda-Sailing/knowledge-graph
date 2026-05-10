---
node_id: concorda-web::src/components/regatta/regatta-detail-sections.tsx::classDisplayName
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 47f46d2f805c1a17189bccd0543a8eafefd1269a72ba6ce14ca9bd15f176293f
status: current
---

# classDisplayName

## Purpose

Formats a class identifier for display within the regatta detail view. It transforms a raw string or a structured object containing `name`, `sail_type`, and `fleet_designator` into a human-readable string. Use this to ensure that class metadata (like sail type or fleet designator) is consistently appended in parentheses to the class name.

## Invariants

- **Input is polymorphic**: Accepts either a `string` or an object with the shape `{ name: string; sail_type?: string; fleet_designator?: string }`.
- **Returns a string**: Always returns a string, even if the input is a complex object.
- **Metadata concatenation**: If an object is provided, `sail_type` and `fleet_designator` are joined by a middle dot (` · `) and wrapped in parentheses.
- **Identity preservation**: If a raw string is passed, it is returned unchanged.

## Gotchas

- **Metadata ordering**: The function relies on the order `[c.sail_type, c.fleet_designator]` to build the string. If the order of these properties is swapped in the input object, the resulting display string will change.
- **Empty metadata handling**: If both `sail_type` and `fleet_designator` are falsy, the function returns only the `name` without parentheses.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: This is a pure formatting helper used within `RegattaDetailSections` to render class lists.

## External consumers

None known.
