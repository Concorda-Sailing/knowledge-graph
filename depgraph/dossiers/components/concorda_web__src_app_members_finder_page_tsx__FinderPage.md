---
node_id: concorda-web::src/app/members/finder/page.tsx::FinderPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 117e87217e6172049944147e366a678b11c4a09e9ed37c111aa76b9a770e0681
status: llm_drafted
---

# FinderPage

## Purpose

The central view for browsing organization members and assets. It provides a tabbed interface to switch between the `CrewFinderPanel` and the `BoatFinderPanel`. It manages the UI state via the URL `tab` search parameter to ensure that the selected view is bookmarkable and survives page refreshes.

## Invariants

- **Default view is "crew"**. If no `tab` parameter is present in the URL, the component defaults to the crew view.
- **State is URL-driven**. The `onChange` handler uses `router.replace` to update the `tab` query parameter rather than using local `useState`.
- **Permission-guarded**. The entire view is wrapped in a `PermissionGate` requiring the `crewfinder.view` permission.

## Gotchas

- **Tab switching via URL**. Per commit `db1379a`, this page was unified to handle both Crew and Boats via a single route with a `tab` param. If you move to a different routing pattern, ensure the `onChange` logic preserves other existing `searchParams`.

## Cross-cutting concerns

- **Auth**: Wrapped in `PermissionGate` with `permission="crewfinder.view"`.
- **Side effects**: The view is a container for `CrewFinderPanel` and `BoatFinderPanel`; changes to the underlying data in those panels will reflect here.

## External consumers

None known.
