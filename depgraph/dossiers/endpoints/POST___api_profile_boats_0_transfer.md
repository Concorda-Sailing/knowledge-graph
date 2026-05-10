---
node_id: POST::/api/profile/boats/{0}/transfer
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d236fb30156d61618d1c1f5b098ed8d5c61ab93ecb23bc08871f8b8f06548bc6
status: llm_drafted
---

# POST /api/profile/boats/{boat_id}/transfer

## Purpose

Initiates a boat ownership transfer by creating an approval request. Instead of an immediate change, it stages a `BoatCrew` row with an `invited` status and triggers a `boat_ownership_transfer` approval flow. This ensures that ownership changes are a multi-step process requiring explicit acceptance from the target person (or other active owners) rather than an instantaneous state change.

## Invariants

- **Requires `current_user` ownership** — The requester must be an existing owner of the boat via `_owner_query`.
- **Returns a generic message** — To prevent member-email enumeration, the response body is identical whether the `new_owner_email` exists in the system or not.
- **Stages, does not complete** — The endpoint creates a `BoatCrew` entry with `status="invited"` and calls `create_request` from `services.approvals`.
- **Input shape** — Expects `TransferBoatRequest` containing a `new_owner_email` string.

## Gotchas

- **Enumeration protection** — Per the docstring, the response is intentionally non-descriptive to avoid acting as a "member-email enumeration oracle."
- **Self-transfer prevention** — If `new_owner.id == current_user.id`, the function returns the generic response without performing any database operations.
- **No-op on active ownership** — If the target is already an active owner, the function treats the request as a no-op and returns the generic response.
- **Approval dependency** — The actual transfer of ownership only occurs when the `boat_ownership_transfer` approval is accepted, as handled by the `services.approvals` logic.

## Cross-cutting concerns

- **Auth**: Requires authenticated user via `require_auth`.
- **Audit**: Triggers an approval request via `create_request`.
- **Side effects**: The `BoatCrew` row status is a state machine; it is flipped to `owner-active` upon approval or deleted upon rejection/expiration.

## External consumers

- `concorda-web::src/lib/api.ts::profileApi.transferBoat`
