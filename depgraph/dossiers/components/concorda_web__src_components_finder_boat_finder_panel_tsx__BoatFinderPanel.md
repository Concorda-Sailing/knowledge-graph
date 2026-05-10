---
node_id: concorda-web::src/components/finder/boat-finder-panel.tsx::BoatFinderPanel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 39ae276abd32e5a5f66c897a8acdc1858d4b0ef6c44d721623d6063d069b9f62
status: llm_drafted
---

# BoatFinderPanel

## Purpose

The `BoatFinderPanel` provides the filtering interface for the member directory, allowing users to narrow down boat and crew profiles by position, race area, and sailing style (ethos). It manages the local state for active filters and orchestrates the fetching of data via `boatfinderApi.list`. It is distinct from `CardGrid` (which handles the visual layout of results) and `ApplyDialog` (which handles the interaction of applying to a boat).

## Invariants

- **Filter-driven fetching**: The `loadBoats` function is triggered by changes to `position`, `raceArea`, or `ethos`.
- **"All" is a valid state**: Selecting "All Positions" or "All Areas" sets the value to `"all"`, which the `loadBoats` logic treats as a signal to omit that parameter from the API request.
- **Constants are required for rendering**: The component relies on `constantsApi.getAll()` to populate the `Select` options for positions and other metadata; if this fails, the dropdowns will be empty.
- **Error handling is silent**: If `boatfinderApi.list` fails, the component catches the error and sets `boats` to an empty array to prevent a crash.

## Gotchas

- **Layout stability**: Per commit `f36708e`, card footers must be pinned to the bottom to ensure a consistent grid height when filtering; ensure any changes to the `Select` components or the grid do not break this alignment.
- **Hardcoded race areas**: The `raceAreas` array is currently hardcoded as `["north", "central", "south"]` within the component rather than being fetched from `constants`. If the API adds a new region, this component will not reflect it until the code is updated.
- **Default App Title**: Per commit `be37238`, the `DEFAULT_CONSTANTS` object includes an `org_name` and `app_title` (defaulting to "MBSA Clubhouse"). If the API returns a different title, it will overwrite this via the `setConstants` effect.

## Cross-cutting concerns

- **Auth**: Relies on `useBoats` (and implicitly the underlying API client) which requires an authenticated session to list member profiles.
- **Side effects**: Changes to the filters in this panel directly control the content rendered in the `CardGrid` component.

## External consumers

None known.
