---
node_id: concorda-web::src/components/boat/boat-positions-config.tsx::ConfigForm
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6989ba384d2a255b2162f6cef6bae5fec886b627e4d4f4686a3bc86e5e75a628
status: current
---

# ConfigForm

## Purpose

The `ConfigForm` is an inline UI component used to create or edit the specific position configurations for a boat. It manages the local state for a boat's name, its `config_type` (e.g., "full"), and the specific counts of various positions (both standard and custom). It is used by the boat owner to define how many crew members are required for specific roles, facilitating the data used by the rest of the boat's profile.

## Invariants

- **`boatId` is required** to identify which boat's configuration is being mutated.
- **`existing` is optional**; if provided, the form initializes with the existing `BoatConfig` values.
- **`onSave` receives a complete `BoatConfig` object**, including the updated `positions` Map converted back to the expected API shape.
- **`customPositions` are tracked separately** from `STANDARD_NAMES` to ensure user-defined roles are preserved during edits.

## Gotchas

- **Mobile layout fragility:** Per commit `189dcf9`, this component requires careful handling of the single-column reflow and stacked actions to ensure the form remains usable on smaller screens.
- **State synchronization:** The `showMore` state is derived from whether the `existing` config contains any non-primary positions; changing this logic can unexpectedly hide/show the expanded configuration UI.

## Cross-cutting concerns

- **Auth**: None (assumes caller handles permissioning for the boat owner).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Updates the boat's profile data, which is consumed by the `BoatProfileTab` and potentially used for calculating crew requirements in other views.

## External consumers

None known.
