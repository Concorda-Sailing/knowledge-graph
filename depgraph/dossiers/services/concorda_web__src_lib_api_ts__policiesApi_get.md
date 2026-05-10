---
node_id: concorda-web::src/lib/api.ts::policiesApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3775de27eecfa6f0cfda4e820c2c2344ce88eb680304d71a171592b6ff1a9b10
status: llm_drafted
---

# policiesApi.get

## Purpose

Fetches the full detail of a specific policy using its unique slug. This is the primary method for retrieving a single policy's data (including `PolicyDetail` properties) from the `/api/policies/{slug}` endpoint. It is distinct from `adminPoliciesApi.listVersions`, which is used for administrative version history, and `adminPoliciesApi.updateDraft`, which is used for modifying existing drafts.

## Invariants

- **Input is a `PolicySlug`** — a string representing the unique identifier for the policy.
- **Returns a `Promise<PolicyDetail>`** — the response contains the core policy properties (name, body, effective date, etc.).
- **Uses `fetchApi` (unauthenticated)** — this is a public-facing read operation and does not require a bearer token.

## Gotchas

- **`PolicyDetail` vs `PolicyVersion`** — while this method returns `PolicyDetail`, the `adminPoliciesApi` methods return `PolicyVersion`. Ensure the consumer is not expecting the `acceptance_count` or `modified` fields if they are relying on this specific endpoint.

## Cross-cutting concerns

- **Auth**: none (public endpoint).
- **Side effects**: used by `PolicyPageView` to populate the main policy view.

## External consumers

- `concorda-web::src/components/policy-page-view.tsx::PolicyPageView`
