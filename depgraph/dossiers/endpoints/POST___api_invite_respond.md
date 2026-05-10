---
node_id: POST::/api/invite/respond
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ba046c5064d3ccf9cb25707b6d6d7441d72b9d3c58b1446682b480ed25efe629
status: current
---

# POST /api/invite/respond

## Purpose

Processes a user's response to a pending invitation (accept or decline). It acts as a thin wrapper around the `dispatch` function to update the invitation state in the database. This is the primary endpoint for finalizing the lifecycle of an invite before it transitions to a completed state.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns `InviteResponseResult`** containing a `kind`, a `status` ("recorded" or "already"), and an optional `detail` string.
- **Input is a single `InviteResponseBody`** containing the specific `id` of the invitation and the user's `decision`.

## Gotchas

- **Uses a unified dispatcher pattern** — per commit `605c924`, the logic for accepting and declining was unified into a single dispatcher to ensure consistent state transitions. Do not attempt to split these into separate endpoints; use the `decision` field in the body to drive the logic.

## Cross-cutting concerns

- **Auth**: Requires a valid `AuthUser` via `require_auth`.
- **Audit**: Y (Updates invitation status in the database via `dispatch`).
- **Side effects**: Triggers updates to the invitation status, which may affect the visibility of the invite in the user's dashboard and the organizer's view.

## External consumers

- `concorda-test::ApiClient.respondToInvite` (Test suite)
- `concorda-web::inviteResponseApi.respond` (Web frontend)
