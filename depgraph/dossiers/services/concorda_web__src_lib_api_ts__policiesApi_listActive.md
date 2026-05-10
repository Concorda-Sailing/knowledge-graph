---
node_id: concorda-web::src/lib/api.ts::policiesApi.listActive
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3980e69e24342207057353be0249d873d093fd69ed695d52e53a34e38faf4606
status: current
---

# policiesApi.listActive

## Purpose

Fetches the list of currently active policies from the backend. This is a public-facing endpoint used to retrieve the base policy details that are currently in effect for the organization. It is distinct from `adminPoliciesApi.listVersions`, which is used for administrative version tracking and history.

## Invariants

- **HTTP Method:** `GET`
- **Endpoint:** `/api/policies`
- **Return Shape:** Returns an array of `PolicyDetail` objects.
- **Data Integrity:** The returned objects represent the current active state of the organization's policies.

## Gotchas

- **Public vs. Admin distinction:** While this method is public, the `adminPoliciesApi` sibling handles the `POST` and `PATCH` operations for versions. Ensure you are not attempting to use `policiesApi.listActive` for administrative updates.
- **Dependency on `fetchApi`:** This method relies on the base `fetchApi` wrapper; unlike `getPending` or `accept`, it does not require an authenticated session to retrieve the list, making it safe for unauthenticated landing pages or registration flows.

## Cross-cutting concerns

- **Auth**: None (uses `fetchApi`, not `fetchApiAuthenticated`).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `RegisterPageContent` in `page.tsx:152` during the registration flow.

## External consumers

None known.
