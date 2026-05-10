---
node_id: concorda-web::src/lib/api.ts::adminPoliciesApi.updateDraft
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d823312d25648d07d3fdc3f75417576e1e420a1e77c0d65af4ad2cf911a37d1c
status: llm_drafted
---

# adminPoliciesApi.updateDraft

## Purpose

Updates an existing policy draft via a `PATCH` request. This is a specialized administrative tool used to modify specific fields of a policy version (such as `name`, `body`, or `effective_date`) without replacing the entire resource. It is distinct from the creation/versioning flow which uses a `POST` to a slug-based endpoint.

## Invariants

- **Method is `PATCH`** — Uses `fetchApiAuthenticated` to perform a partial update.
- **Payload is a `Partial` of the version object** — Accepts a subset of `name`, `version`, `body`, `effective_date`, and `is_material_change`.
- **Requires `contract_uuid`** — The endpoint is keyed by the specific contract identifier.
- **Returns `Promise<PolicyVersion>`** — The response shape must match the `PolicyVersion` type.

## Gotchas

- **Requires administrative privileges** — Because it uses `fetchApiAuthenticated`, the caller must have an active session with the appropriate admin scopes.
- **Strict field typing** — The `payload` expects specific keys; attempting to pass extra metadata not defined in the `Partial` type may lead to unexpected behavior if the backend does not strip unknown fields.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level access).
- **Side effects**: Updates to policy drafts may trigger downstream notifications or status changes in the policy lifecycle.

## External consumers

None known.
