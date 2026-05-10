---
node_id: concorda-web::src/app/members/admin/policies/[slug]/page.tsx::isValidSlug
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 84635ca5055044102afbd4f399255d7a02fc0f7e9d92c1b1015ada5a0dea822a
status: llm_drafted
---

# isValidSlug

## Purpose

A type guard used to validate that a URL parameter matches one of the three allowed policy types: `tos`, `code_of_conduct`, or `privacy_policy`. It ensures that the `slug` string is safely cast to the `PolicySlug` type before being passed to `adminPoliciesApi.listVersions` or `adminPoliciesApi.publish`.

## Invariants

- **Strict string matching**: Only returns true for the exact strings `"tos"`, `"code_of_conduct"`, or `"privacy_policy"`.
- **Type narrowing**: Acts as a type guard (`slug is PolicySlug`) to satisfy TypeScript requirements for the `adminPoliciesApi` methods.
- **Null fallback**: If the slug is invalid or missing, the `PolicyDetailPage` renders an "Unknown policy" view rather than attempting to fetch data.

## Gotchas

- **Manual sync required**: If a new policy type is added to the backend/API, it must be added to the `SLUG_PUBLIC_PATH` record and this `isValidSlug` function simultaneously, or the UI will treat the new policy as an "Unknown policy."

## Cross-cutting concerns

- **Auth**: Relies on `adminPoliciesApi` which requires authenticated admin access.
- **Side effects**: The `slug` determines which version history is fetched and which policy is updated during the `handlePublish` workflow.

## External consumers

None known.
