---
node_id: POST::/api/policies/admin/{0}/versions
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: de5cc3ba88279bac12c842d83cfb81f8b1dbc1fc0052c78f9bd70927eef4bdf6
status: current
---

# POST /api/policies/admin/{slug}/versions

## Purpose

Publishes a new active version of a policy for a given slug. It is used to transition a draft into a live state, automatically deactivating any existing active version for that slug to ensure only one version is "live" at a time. Use this instead of `update_draft` when the policy is ready for user acceptance.

## Invariants

- **Method is `POST`** to `/api/policies/admin/{slug}/versions`.
- **Requires `admin.policies.manage` permission** via the `require_permission` dependency.
- **Atomically deactivates previous versions** by setting `is_active=False` for the existing active row with the same slug.
- **Returns a `PolicyVersion` object** with `acceptance_count` initialized to `0`.
- **`is_material_change` flag determines UX behavior**: if `True`, users are re-prompted to accept the policy on their next request.

## Gotchas

- **Duplicate version strings cause a 409 Conflict.** The endpoint explicitly checks for existing versions to prevent silent overwrites and maintain legible audit trails.
- **The `is_material_change` flag is critical for the "error-alert pipeline".** Per commit `da1589d`, this flag drives whether users see a new alert/prompt for the updated policy.
- **Deactivation is not a deletion.** The previous version remains in the DB but is marked `is_active=False`.

## Cross-cutting concerns

- **Auth**: Requires `admin.policies.manage` permission.
- **Audit**: Y (Updates `is_active` status and creates new `Contract` rows).
- **Side effects**: Triggers the "error-alert pipeline" for users if `is_material_change` is true.

## External consumers

- `concorda-web::src/lib/api.ts::adminPoliciesApi.publish`
