---
node_id: concorda-web::src/app/members/crew/page.tsx::CrewRedirect
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1325f42d8dd4641516e78d0261013c9a0755d9f2601261df8fd6124e6837933e
status: current
---

# CrewRedirect

## Purpose

A transient client-side redirect component used to transition users from the `/members/crew` path to the main members directory with the correct query parameter. It serves as a loading state (displaying a `Loader2` spinner) while the `next/navigation` router performs the replacement. This ensures that users hitting the legacy or direct path are seamlessly moved to the tabbed interface without manual URL manipulation.

## Invariants

- **Uses `router.replace`** — This prevents the redirecting page from cluttering the browser history, ensuring the user doesn't get stuck in a "back-button loop" when trying to return to a previous page.
- **Client-side execution only** — The component is marked `"use client"` and relies on `useEffect` to trigger the side effect after the initial mount.
- **Visual feedback** — Always renders a centered `Loader2` spinner to prevent a blank screen during the navigation transition.

## Gotchas

- **UX improvements in `4cd1587`** — This component is part of the broader "directory redesign" and "UX improvements" mentioned in commit `4cd1587`. Changes to the routing structure in the members directory should be checked against this redirect to ensure the `?tab=crew` parameter remains the intended destination.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Redirects users to the main members directory view.

## External consumers

None known.
