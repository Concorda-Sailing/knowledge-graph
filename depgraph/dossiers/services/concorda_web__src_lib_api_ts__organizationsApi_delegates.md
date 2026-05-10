---
node_id: concorda-web::src/lib/api.ts::organizationsApi.delegates
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3f905a21e7b466af701d0af2175148e032f59a44f6ce8ec0cfeef7b9e439d354
status: current
---

# organizationsApi.delegates

## Purpose

Fetches the list of organization delegates via the `/api/organizations/delegates` endpoint. This is a specialized read-only method within the `organizationsApi` object, distinct from the standard `list` or `get` methods which target specific organization IDs or types. Use this when the UI needs to display the high-level administrative/representative structure of the organization rather than the organization's core metadata.

## Invariants

- **Returns a Promise of `DelegateInfo[]`**.
- **Uses `fetchApi`** — relies on the standard authenticated fetch wrapper for the organization context.
- **Endpoint is static** — does not accept arguments or query parameters.

## Gotchas

- **Implicit dependency on organization context** — because it uses `fetchApi`, the request relies on the active organization state/token established in the session.

## Cross-cutting concerns

- **Auth**: Uses `fetchApi` (requires an authenticated session).
- **Side effects**: None.

## External consumers

- `concorda-web::src/app/members/clubs/page.tsx` (via `MemberClubsPage`)
