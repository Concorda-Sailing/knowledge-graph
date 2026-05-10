---
node_id: concorda-api::schemas/boat.py::PunchlistItemUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 574505073edcfd2bfe8c274ae109e7dcba823708c405d3c91c180265a153a0ff
status: current
---

# PunchlistItemUpdate

## Purpose

The schema for partial updates to a punchlist item. It is used by the `PUT /api/boats/{boat_uuid}/punchlist/{item_id}` endpoint to allow clients to modify specific fields of an existing item without providing the full object. Use this instead of `PunchlistItemCreate` when performing an update operation.

## Invariants

- **All fields are optional.** Every field in the class is typed as `Optional` to support partial updates via PATCH-style logic in the router.
- **`importance` must be one of `high`, `medium`, or `low`.**
- **`status` must be one of `open`, `in_progress`, or `done`.**
- **`assigned_to_uuid` accepts a string.** This is used to link a person to a specific task.

## Gotchas

- **Recent migrations (commit `68a7508`)** introduced refinements to the boat/punchlist router; ensure any logic relying on this schema respects the updated router structure for boat-specific sub-resources.

## Cross-cutting concerns

- **Auth**: Handled by the boat router's dependency injection (requires authenticated user with boat access).
- **Side effects**: Updates to `status` or `assigned_to_uuid` may trigger notifications in the boat management dashboard.

## External consumers

- Web app (Concorda Dashboard) via the boat-specific API routes.

## Open questions

- Should the `importance` and `status` fields be converted to strict `Enum` types to enforce validation at the schema level rather than relying on string literals?
