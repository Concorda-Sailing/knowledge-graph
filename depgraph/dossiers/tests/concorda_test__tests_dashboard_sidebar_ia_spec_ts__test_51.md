---
node_id: concorda-test::tests/dashboard/sidebar-ia.spec.ts::test@51
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7bfd8468a3a7b29cccff297f44792a7f9181723781520002add354a43b180b6a
status: current
---

# /members/boatfinder redirects to /members/finder?tab=boats

## Purpose

Verifies that the legacy "finder" URLs (`/members/crewfinder` and `/members/boatfinder`) correctly redirect to the modern `/members/finder` route with the appropriate `tab` query parameter. This ensures backward compatibility for bookmarks or legacy internal links within the dashboard.

## Invariants

- **Redirects to `/members/finder`** — both legacy paths must land on the unified finder route.
- **Appends correct `tab` parameter** — `crewfinder` must map to `tab=crew` and `boatfinder` must map to `tab=boats`.
- **Requires authenticated state** — uses `storageState: 'auth-states/member.json'` to ensure the redirect is tested within a logged-in session context.

## Gotchas

- **Mobile viewport stability** — per commit `69f60cc`, assertions in this suite (specifically regarding tab lists and aria-selected states) require waiting for the tab list to be present to avoid flakiness on mobile viewports.

## Cross-cutting concerns

- **Auth**: Uses `auth-states/member.json` via `test.use`.
- **Side effects**: Validates the routing integrity of the "finder" feature components.

## External consumers

None known.
