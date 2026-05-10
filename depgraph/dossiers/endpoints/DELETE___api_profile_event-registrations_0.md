---
node_id: DELETE::/api/profile/event-registrations/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 989300496f4a1a58491839e7d2f39312b0004c3ca3e7b6546cf5a066173199cc
status: current
---

# DELETE /api/profile/event-registrations/{registration_id}

## Purpose

Performs a soft delete on an event registration by updating its status to `Cancelled`. This endpoint is used when a user wants to withdraw from an event they have previously joined. It is distinct from a hard delete; the record remains in the database for historical/audit purposes but is no longer an active registration.

## Invariants

- **HTTP Method**: `DELETE`.
- **Auth**: Requires a valid session via `require_auth`.
- **Ownership**: The `current_user.id` must match the `reg.person_id` of the registration.
- **Return Shape**: Returns a JSON object with a `"message"` string upon success.
- **Status Transition**: Only transitions a registration from an active state to `"Cancelled"`.

## Gotchas

- **Soft Delete Only**: This does not remove the row from the database; it only sets `reg.status = "Cancelled"`.
- **Idempotency/State Guard**: If the registration is already in a `"Cancelled"` state, the API returns a `400 Bad Request`. This prevents redundant state-change logic from running.
- **IDOR Protection**: The endpoint explicitly checks `reg.person_id != current_user.id` to prevent users from cancelling other people's registrations.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to ensure the requester is a logged-in user.
- **Audit**: Performs a soft delete (status update) rather than a row deletion.
- **Side effects**: Changing this status may affect the visibility of the user's participation in event-related views or rosters.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.cancelEventRegistration`
