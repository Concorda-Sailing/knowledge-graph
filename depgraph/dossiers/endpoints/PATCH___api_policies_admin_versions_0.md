---
node_id: PATCH::/api/policies/admin/versions/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7e12fbaf73d691283ac90445adf11cf00b207bde1c6070209852d4ae46c35419
status: llm_drafted
---

# PATCH /api/policies/admin/versions/{contract_uuid}

## Purpose

Allows an administrator to modify a draft policy version before it is finalized. This is a "correction" window: it enables fixing typos or metadata (name, version string, body, effective date) while the version is still in a draft state. Once a `PersonContractAcceptance` is recorded for this `contract_uuid`, this endpoint becomes unusable to prevent mutating a contract that users have already legally interacted with.

## Invariants

- **HTTP Method:** `PATCH`.
- **Auth Requirement:** Requires `admin.policies.manage` permission via `require_permission`.
- **Strict Lock Condition:** Returns `409 Conflict` if any `PersonContractAcceptance` exists for the `contract_uuid`.
- **Version Uniqueness:** If updating the `version` field, the new version string must not clash with an existing version for the same `slug`.
- **Return Shape:** Returns a `PolicyVersion` object with `acceptance_count` hardcoded to `0` (as this is a draft-only view).

## Gotchas

- **The "Acceptance Lock":** Per the docstring, "Once anyone accepts, the version is locked." If an admin needs to change a policy that has already been accepted, they cannot use this endpoint; they must instead create a new version.
- **Collision Logic:** The check for `clash` (lines 408-416) ensures that you cannot change a version number to one that already exists for that specific slug.

## Cross-cutting concerns

- **Auth**: Guarded by `require_permission("admin.policies.manage")`.
- **Audit**: N/A.
- **Side effects**: Changes to the policy body or versioning will affect the display of the policy in the member-facing view once the version is active.

## External consumers

- `concorda-web` (via `adminPoliciesApi.updateDraft`).

## Open questions

- Should there be a way to "unlock" a version if a mistake is made after acceptance, or is the "publish a new version instead" workflow the strictly enforced legal standard?
