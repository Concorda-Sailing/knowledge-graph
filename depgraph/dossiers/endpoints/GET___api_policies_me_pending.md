---
node_id: GET::/api/policies/me/pending
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0e7725a832592d6f352fa4502e3c79fd2d7f70f2341aa91ef2c292253d5cd128
status: current
---

# GET /api/policies/me/pending

## Purpose

Retrieves a list of active policies that the authenticated user has not yet accepted. This is used to drive the "pending action" UI, such as the policy acceptance banner or modal. It is distinct from the general policy list as it filters specifically for the current user's unaccepted versions via `pending_policies_for`.

## Invariants

- **HTTP Method**: `GET`.
- **Authentication**: Requires a valid session via `require_auth`.
- **Return Shape**: Returns a `list[PolicyDetail]`.
- **Empty State**: Returns an empty list `[]` if no policies are pending, rather than a 404.

## Gotchas

- **Versioned Policies**: Per commit `da1589d`, this endpoint now supports versioned policies. The returned `PolicyDetail` includes the `version` and `is_material_change` flag to ensure the UI can distinguish between standard updates and significant legal changes.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` to identify the `current_user`.
- **Side effects**: Used by the web frontend to trigger the policy acceptance workflow (e.g., showing the "Accept Terms" banner).

## External consumers

- `concorda-web` (via `policiesApi.getPending`)
- `concorda-test` (via `ApiClient.getPendingPolicies`)
