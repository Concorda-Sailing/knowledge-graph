---
node_id: concorda-web::src/components/dashboard/event-plan-panel.tsx::InlineConfigCreate
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fbddad365fc28ba9eedf81923a52a7143fb9d1477fe7af38560c768500806165
status: llm_drafted
---

# InlineConfigCreate

## Purpose

A modal-like inline component for creating a new `BoatConfig` for a specific boat. It allows users to name a configuration and select a set of positions (e.g., Bow, Pit, Mast) to define a custom layout. This is used when a user needs to define a specific equipment or crew setup that is unique to a single boat.

## Invariants

- **Requires `boatId`** to associate the new configuration with the correct boat via `profileApi.createBoatConfig`.
- **`name` cannot be empty or whitespace**; the `handleCreate` function returns early if `!name.trim()`.
- **At least one position must be selected**; `counts.size === 0` prevents submission.
- **Returns a `BoatConfig` object** via the `onCreated` callback upon successful API response.
- **Uses `config_type: "full"`** as the hardcoded type for all new inline configurations.

## Gotchas

- **Position mapping relies on `QUICK_POSITIONS`** — if a position is selected that doesn't exist in the `QUICK_POSITIONS` constant, the `location_x` and `location_y` default to `50` (center) via the nullish coalescing in the map function.
- **Recent refactor (commit `2e089b2`)** — ensure that any logic interacting with this component respects the new scope where pool and configuration APIs are strictly tied to a specific boat.

## Cross-cutting concerns

- **Auth**: Requires authenticated access to `profileApi.createBoatConfig`.
- **Side effects**: Successful creation triggers `onCreated`, which typically updates the parent `EventPlanPanel` state to reflect the new configuration.

## External consumers

None known.
