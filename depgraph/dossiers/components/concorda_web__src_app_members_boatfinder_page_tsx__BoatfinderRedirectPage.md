---
node_id: concorda-web::src/app/members/boatfinder/page.tsx::BoatfinderRedirectPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 03fd91edf387dce7bd8cca7d41cb98c86207cc007ade5f7c0baa58ef51b3990d
status: current
---

# BoatfinderRedirectPage

## Purpose

Acts as a legacy routing shim to redirect users from the deprecated `/boatfinder` path to the new unified `/finder` interface. It uses `router.replace` to ensure the redirect doesn't clutter the browser history, landing the user specifically on the `?tab=boats` view.

## Invariants

- **Redirects to `/members/finder?tab=boats`** — the destination is hardcoded to ensure the user lands on the boat-specific view of the new finder.
- **Returns `null`** — the component renders nothing while the `useEffect` hook executes the navigation.
- **Client-side only** — uses `"use client"` and `next/navigation` to handle the transition within the browser.

## Gotchas

- **Legacy path consolidation** — per commit `5c8c32a`, this page is part of the effort to redirect both `/crewfinder` and `/boatfinder` to the unified `/finder` route. Do not attempt to move the logic to a server-side redirect if the goal is to maintain the client-side transition behavior established in this commit.

## Cross-cutting concerns

- **Auth**: none (relies on the parent layout's authentication guards).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: Redirects users to the unified finder interface, which is the primary entry point for boat discovery.

## External consumers

None known.
