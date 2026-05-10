---
node_id: concorda-web::src/components/profile/boat-exclusion-list.tsx::BoatExclusionList
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c9e3fa42d645b80c9de15f7f52c3ca5e842ba498ae1dece37a8c49b7f7c8bda
status: current
---

# BoatExclusionList

## Purpose

Manages the selection and display of boats that are excluded from contact or marked as "no contact" for a user's profile. It provides a searchable interface to resolve boat IDs into human-readable labels (sail number, name, and owner) using the `crewfinderApi`. Use this component when a user needs to manage visibility/contact restrictions for specific vessels within their profile settings.

## Invariants

- **Input is dual-array based**: Takes `excludedBoatIds` and `noContactBoatIds` separately to distinguish between general exclusion and strict no-contact status.
- **Label resolution is asynchronous**: Uses `crewfinderApi.searchBoats("")` on mount to fetch a mapping of IDs to labels to ensure the UI shows names instead of raw UUIDs.
- **Fallback to ID**: If the API call fails or a boat cannot be found in the map, the component must fall back to displaying the raw ID as the label to prevent empty/broken UI.
- **`onChange` signature**: Returns two arrays: `(excludedBoatIds: string[], noContactBoatIds: string[])`.

## Gotchas

- **Race condition on mount**: The `useEffect` uses a `resolved` state to ensure the initial ID-to-label mapping only happens once. If `resolved` is toggled or the component re-renders with new IDs, the mapping logic might trigger unexpectedly if not handled carefully.
- **Search debounce**: Uses a `setTimeout` via `debounceRef` to prevent rapid-fire API calls during typing. If implementing a custom search handler, ensure the `clearTimeout` logic is preserved to avoid `crewfinderApi` spam.

## Cross-cutting concerns

- **Auth**: Requires authenticated access to `crewfinderApi.searchBoats`.
- **Side effects**: Updates to this component's state are passed up via `onChange`, which eventually affects the user's profile visibility settings.

## External consumers

None known.
