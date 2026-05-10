---
node_id: concorda-web::src/app/members/crewfinder/page.tsx::CrewfinderRedirectPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1f4e1204deb40633747e7a6e2fbfcaf94cff5e7e0f9d3e93c96b537cb1d54ed0
status: llm_drafted
---

# CrewfinderRedirectPage

## Purpose

A lightweight client-side redirect component used to bridge legacy URL paths to the new unified finder architecture. It performs a single `router.replace` to move users from the deprecated `/members/crewfinder` path to the `/members/finder?tab=crew` route. This ensures backward compatibility for bookmarks or hardcoded links without requiring a server-side redirect.

## Invariants

- **Returns `null` during the transition.** The component renders nothing to avoid a flash of empty UI before the `useEffect` triggers the navigation.
- **Uses `router.replace` instead of `router.push`.** This prevents the legacy path from cluttering the browser history stack, ensuring the "Back" button behaves as if the user never hit the redirect.
- **Client-side execution only.** The `"use client"` directive is mandatory as it relies on the `useRouter` hook from `next/navigation`.

## Gotchas

- **Legacy path consolidation.** Per commit `5c8c32a`, this page is part of a larger effort to redirect both `/crewfinder` and `/boatfinder` to the unified `/finder` route. Do not attempt to add logic or UI here; it is strictly a routing shim.

## Cross-cutting concerns

- **Auth**: None. The redirect happens at the routing level, but the destination (`/members/finder`) is subject to standard member authentication guards.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Redirects users to the `finder` component tree, which manages the state for the "crew" tab.

## External consumers

None known.
