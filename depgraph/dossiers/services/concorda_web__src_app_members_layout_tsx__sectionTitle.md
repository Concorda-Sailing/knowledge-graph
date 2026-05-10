---
node_id: concorda-web::src/app/members/layout.tsx::sectionTitle
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 750cd2af67739fb2e16d1f5395b0d04de10b709a587c061ae16c899b6a82f90d
status: current
---

# sectionTitle

## Purpose

The `sectionTitle` function generates the text label for the mobile top bar in the members' dashboard. It maps specific URL paths to human-readable strings so that users on small screens have clear context of their current location. It acts as a fallback mechanism, returning "Dashboard" for any path that does not match the defined patterns.

## Invariants

- **Input is a string representing the current pathname.**
- **Returns a string.** The output is used directly in a `<span>` within the mobile header.
- **Fallback behavior is mandatory.** If the path does not match a specific sub-route (e.g., `/members/regattas`), it must return "Dashboard" to ensure the header is never empty.
- **Regatta title is dynamic.** The regatta path includes a dynamic year via `new Date().getFullYear()`.

## Gotchas

- **Path-based matching is brittle.** The function relies on `pathname.startsWith`. If a route structure changes (e.g., moving `/members/inbox` to a different parent), the title will revert to "Dashboard" without warning.
- **Recent route additions require manual updates.** Per commit `2c92df7`, the `/members/inbox` route was recently added; failure to add a new path to this function results in the UI displaying "Dashboard" instead of the actual page name.

## Cross-cutting concerns

- **Auth**: The `DashboardLayout` (which consumes this) is gated by `isAuthenticated`. If the user is not authenticated, the layout returns a loader, and `sectionTitle` is not executed.
- **Side effects**: Updates to the mobile top bar label occur when the `pathname` changes, as the layout is a client component reacting to navigation.

## External consumers

None known.
