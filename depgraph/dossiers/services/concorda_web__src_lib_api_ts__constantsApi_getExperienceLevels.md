---
node_id: concorda-web::src/lib/api.ts::constantsApi.getExperienceLevels
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eb11b2d00ed1599f5b5a72d253af375f275f3d1025fd9c20fe3c0a80807130b2
status: current
---

# constantsApi.getExperienceLevels

## Purpose

Fetches the list of available experience levels from the constants API. This is used to populate selection menus (like skill levels or proficiency ratings) to ensure the frontend uses the exact strings and identifiers expected by the backend. Use this instead of hardcoding strings to prevent mismatch errors during form submission.

## Invariants

- **Returns `ExperienceLevel[]`** — the response is a collection of objects representing experience tiers.
- **Uses `fetchApi`** — unlike `profileApi` or `getUserPermissions`, this uses the unauthenticated `fetchApi` helper because constants are public-facing.
- **Endpoint is `/api/constants/experience-levels`** — follows the standard constants pattern used by `getPositions`.

## Gotchas

- **Implicit dependency on backend seeding** — if the backend's constant management UI or seed scripts are not updated, this will return an empty list or outdated tiers, potentially breaking profile completion flows.

## Cross-cutting concerns

- **Auth**: none (uses unauthenticated `fetchApi`).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: used by profile/onboarding flows to populate experience selection inputs.

## External consumers

None known.
