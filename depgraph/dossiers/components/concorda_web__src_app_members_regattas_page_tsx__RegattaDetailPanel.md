---
node_id: concorda-web::src/app/members/regattas/page.tsx::RegattaDetailPanel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e893744f371b18c94afab235b5d76d56d5bf243110209efd7479be39c35ab62d
status: llm_drafted
---

# RegattaDetailPanel

## Purpose

Displays the detailed view of a specific regatta, including its relationship to parent series and organizing clubs. It serves as the primary information hub for a selected regatta, providing context like the organizer, the roster status, and whether the user is opted into the crew-finder feature. It is distinct from the `RegattaCard` by providing deep-link data (Series, Organization) and user-specific state (Opt-in status) that the list view does not surface.

## Invariants

- **`tz` must be passed from the parent** to ensure `formatInOrgTz` renders the regatta start/end times in the organization's local time rather than the user's browser time.
- **`regatta.id` is the primary key** for fetching the match roster via `regatiaApi.getMatchRoster`.
- **`regatta.series_uuid` and `regatta.oa_uuid` are optional**; the component must handle null/undefined values by setting `parentSeries` or `organizer` to `null` without crashing.
- **`onAdd` is a callback** intended to trigger the addition of the regatta to the user's schedule.

## Gotchas

- **Timezone rendering is critical.** Per commit `f444b4c`, all backend datetimes must be rendered using the provided `tz` via `formatInOrgTz` to avoid displaying incorrect local browser times for race starts.
- **The "Accepting-Crew" badge logic is sensitive.** Per commit `b5в15da5`, the UI relies on the `regatta` object's properties to drive the visual state of the "Accepting-Crew" badge; ensure the `regatta` object passed in contains the latest `crew_finder` or `toggle` state.
- **Race-condition protection is required.** The `useEffect` hooks use a `cancelled` flag to prevent setting state on unmounted components, which is necessary because `profileApi.get()` and `regattaApi.getMatchRoster()` are asynchronous.

## Cross-cutting concerns

- **Auth**: Uses `profileApi.get()` to check the user's `crewfinder.opt_in` preference, which determines the `optedIn` state.
- **Side effects**: The data fetched here (Roster, Series, Organizer) informs the visual state of the "Accepting-Crew" badge and the "Schedule" view.

## External consumers

None known.
