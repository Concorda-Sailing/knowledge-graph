---
node_id: GET::/api/invite/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 27c9dc2a821a5d7fd13d31bb587a4327dffb09c6523b91150a05a1059ed7f49a
status: llm_drafted
---

# GET /api/invite/{invite_code}

## Purpose

Retrieves the metadata associated with a specific invite code to allow a user to preview their upcoming role before committing to an acceptance. It distinguishes between "crew" invites (existing members) and "pending" invites (new users) to determine whether to show an email address or a placeholder. This endpoint is the primary entry point for the "Invite Preview" UI.

## Invariants

- **No authentication required** for the GET request to ensure unauthenticated users can view the landing page via the email link.
- **Returns a 404** if the `invite_code` is invalid, expired, or already used.
- **Output shape includes `has_account`** (boolean) and `invite_type` ("crew" vs "pending") to drive the UI state.
- **Email normalization** is used during the lookup for "pending" invites to ensure the `has_account` check is resilient to casing or whitespace differences.

## Gotchas

- **Security/IDOR protection:** While the GET endpoint is unauthenticated, the subsequent `POST /{invite_code}/accept` requires `require_auth`. Recent security fixes (commit `c9a7c41` and `9871b1c`) ensure that users cannot spoof identity or bypass the `person_uuid` check when accepting a crew invite.
- **Email matching logic:** For "pending" invites, the system compares the `record.email` against the `Person` table using `_normalize_email` and `func.lower` to prevent mismians due to Unicode/whitespace discrepancies.

## Cross-cutting concerns

- **Auth**: GET is unauthenticated; POST requires `require_auth`.
- **Websocket**: The `POST /{invite_code}/accept` endpoint triggers a `broadcast_event(BOAT_CREW_UPDATED, boat.id)`.
- **Side effects**: Successful acceptance updates the `BoatCrew` status and triggers updates to the boat's crew list.

## External consumers

- `concorda-web::src/lib/api.ts::inviteApi.getInvite`
