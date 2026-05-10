---
node_id: concorda-web::src/components/boat/club-autocomplete-input.tsx::ClubAutocompleteInput
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d135cebd787720e118c5b242009309f4ac65f0f69adfaebeb10e22acd788f395
status: llm_drafted
---

# ClubAutocompleteInput

## Purpose

Provides an autocomplete input for selecting a club from a pre-fetched list of organizations. It uses a standard HTML `<datalist>` to suggest names, but maps the selection back to a structured object containing the club's name, city, and state via the `onChange` callback. Use this when a user needs to select an existing organization that requires associated geographic metadata (city/state) for the boat's profile.

## Invariants

- **Returns structured data.** The `onChange` callback must receive an object with `{ name: string, city?: string, state?: string }` rather than just a string.
- **Datalist mapping is name-based.** The component relies on an exact string match between the input value and the `c.name` in the `clubs` array to populate the city and state.
- **`autoComplete="off"` is hardcoded.** This prevents browser-native autocomplete from interfering with the custom datalist suggestions.

## Gotchas

- **UX polish dependency.** Per commit `f8efc3a`, this component is part of the "UX polish across signup, resume, and boat location" effort; changes to the input behavior may impact the perceived smoothness of the boat location setup flow.
- **Async loading race conditions.** The `useEffect` uses a `mounted` flag to prevent setting state on an unmounted component, but if `loadClubs()` takes significant time, the user might interact with an empty list before the data arrives.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Updates the boat profile location data via the parent component's `onChange` handler.

## External consumers

None known.
