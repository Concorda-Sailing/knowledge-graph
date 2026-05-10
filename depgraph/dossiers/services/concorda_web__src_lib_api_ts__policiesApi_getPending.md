---
node_id: concorda-web::src/lib/api.ts::policiesApi.getPending
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e251a0880b7c624fa5317ef746d6d3ba3036092b090138d6a5e53d62b1ea978f
status: llm_drafted
---

# policiesApi.getPending

## Purpose

Fetches the list of policy details currently pending action for the authenticated user. This is the primary endpoint for the "Accept/Decline" workflow in the user dashboard. Use this instead of `listActive` when you need to present actions that require user consent or signature.

## Invariants

- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the request is scoped to the logged-in user.
- **Returns an array of `PolicyDetail`** — Each object includes metadata like `acceptance_count`, `created`, and `modified`.
- **Read-only fetch** — This specific method only retrieves data; actual state transitions (accepting/declining) must be handled via `policiesApi.accept`.

## Gotchas

- **Requires active session** — Because it uses `fetchApiAuthenticated`, it will fail if the user's session has expired or if the token is missing.
- **Dashboard dependency** — Per commit `e02996c`, this is used to drive the "incoming co-owner invites" display in the dashboard; changes to the return shape may break the unread/pending indicator logic.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (bearer token required).
- **Side effects**: Drives the "incoming co-owner invites" UI in the dashboard.

## External consumers

- `AcceptPoliciesPage` in the web app.
