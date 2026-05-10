---
node_id: concorda-web::src/lib/api.ts::adminPoliciesApi.publish
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e78eb542df7513f75720f7251586ca2c1fc1eafa225915b9a189f9563d1966e0
status: current
---

# adminPoliciesApi.publish

## Purpose

The `adminPoliciesApi.publish` method handles the finalization of a policy version. It posts a completed policy payload to the administrative endpoint for a specific policy slug. Use this method when a user has finished editing a draft and intends to make the version live/effective.

## Invariants

- **HTTP Method is `POST`** — unlike `updateDraft` which uses `PATCH`.
- **Requires a `slug`** — the unique identifier for the policy being published.
- **Payload structure is strict** — must include `name`, `version`, `body`, and `effective_date` (as a string), plus the `is_material_change` boolean.
- **Uses `fetchApiAuthenticated`** — requires a valid administrative session/token to execute.
- **Returns a `PolicyVersion` object** — the single version object that was just created/published.

## Gotchas

- **Payload mismatch** — if the `payload` object does not strictly match the expected keys (e.g., missing `is_material_change`), the API will reject the request.
- **`effective_date` format** — the `effective_date` must be a valid ISO string; passing a raw Date object or incorrect format will fail at the API layer.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`; requires administrative privileges.
- **Side effects**: Successful publication likely triggers downstream updates to policy-related views or notifications, though the specific UI refresh logic is handled by the component-level state management.

## External consumers

- `PolicyDetailPage` in `concorda-web::src/app/members/admin/policies/[slug]/page.tsx`.
