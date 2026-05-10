---
node_id: concorda-web::src/components/boat/boat-positions-config.tsx::PresetButton
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2d3e57670e4efd84b159bb8997b9e07b2685af857a9b6d60873f0552353ea643
status: current
---

# PresetButton

## Purpose

The `PresetButton` is a specialized UI component used to quickly instantiate a pre-defined boat configuration. It abstracts the complexity of mapping a human-readable preset name to a specific technical `BoatConfig` object. An agent should use this when a user needs to apply a standard set of positions (e.g., "Double-handed") rather than manually toggling individual position rows.

## Invariants

- **Requires `boatId`** — The button must be associated with a specific boat instance to call `profileApi.createBoatConfig`.
- **Calls `profileApi.createBoat config`** — The creation process is an asynchronous side effect that triggers a backend write.
- **Uses `positionsToApi`** — The `positions` map must be transformed via this helper to match the expected API schema before submission.
- **Returns `config: BoatConfig`** — Upon successful creation, the `onCreated` callback receives the full configuration object.

## Gotchas

- **Mobile layout sensitivity** — Per commit `189dcf4`, the surrounding configuration section requires careful handling of column reflows to ensure buttons remain accessible on small screens.
- **Stateful "Creating" state** — The button enters a `creating` state (showing `...`) during the async call to prevent double-submission; ensure any logic involving this button accounts for the `disabled={creating}` prop.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi` which requires an authenticated session.
- **Rate limit**: None (though the parent component/API may have limits for configuration updates).
- **Side effects**: Triggers a refresh of the boat configuration state via the `onCreated` callback.

## External consumers

None known.
