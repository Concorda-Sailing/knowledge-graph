---
node_id: GET::/api/policies
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3d5ac66b174593f874c69b0f24662d8f37c65b5e4971e7ec67471c8745eb4f53
status: llm_drafted
---

# GET /api/policies

## Purpose

Fetches the list of currently active and published policies. This is a public endpoint used primarily by the registration form to render the mandatory policy acceptance checkboxes. It is distinct from the `/me/pending` endpoint, which is user-specific and requires authentication to determine which policies a specific user has yet to sign.

## Invariants

- **HTTP Method is `GET`**.
- **Returns a list of `PolicyDetail` objects.** Each object contains `id`, `slug`, `name`, `version`, `body`, `effective_date`, and `is_material_change`.
- **Filters by `is_active == True`**. Only policies marked as active in the database are returned.
- **Orders by `slug`**. The list is returned in alphabetical order by the policy slug.

## Gotchas

- **Versioned policies requirement**: Per commit `da1589d`, this endpoint is part of the new versioned policies and error-alert pipeline. Changes to the `PolicyDetail` schema or the way `is_material_change` is flagged will directly impact the registration form's ability to signal required user actions.

## Cross-cutting concerns

- **Auth**: None (this specific endpoint is public).
- **Side effects**: Used by the registration form to render the policy acceptance UI.

## External consumers

- `concorda-web` (via `policiesApi.listActive`).
