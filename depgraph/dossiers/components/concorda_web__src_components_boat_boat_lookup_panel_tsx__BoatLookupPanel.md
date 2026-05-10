---
node_id: concorda-web::src/components/boat/boat-lookup-panel.tsx::BoatLookupPanel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: af9ca05f2e44436bcde70278f48e9133dd17c39dbc5e37818362811d33b021eb
status: current
---

# BoatLookupPanel

## Purpose

Provides a real-time conflict detection UI when a user is entering boat registration data. It monitors the `sailNumber` and `boatName` props to determine if the boat is already registered in the system via `boatApi.lookup`. If a match is found, it displays an alert prompting the user to either request co-owner status or edit the existing entry, preventing duplicate registrations from going unnoticed.

## Invariants

- **Debounced lookup** — Uses a 400ms `setTimeout` to prevent excessive API calls while the user is typing.
- **Input validation** — If `sailNumber` or `boatName` are empty or whitespace-only, the component returns `null` and triggers `onClear`.
- **Match shape** — A successful match must contain `boat_uuid`, `boat_name`, and an `owner_names` array (defaults to `[]`) to render the alert correctly.
- **Prop-driven state** — The component is a controlled observer; it does not manage the boat's identity itself, but reacts to changes in the parent's input state.

## Gotchas

- **Conflict detection is a recent addition** — Per commit `0c63d9e`, this panel was specifically added to handle sail-number conflicts that were previously unhandled in the registration flow.
- **Async race conditions** — The `useEffect` includes a cleanup function `clearTimeout(t)` to ensure that if the user types rapidly, stale lookup results from previous keystrokes do not overwrite the current state.

## Cross-cutting concerns

- **Auth**: Relies on `boatApi.lookup` which requires a valid session/token to check existing registrations.
- **Side effects**: Triggers `onClear` on the parent component when inputs are cleared, and provides hooks for `onRequestCoowner` and `onEditEntry` to drive the registration workflow.

## External consumers

None known.
