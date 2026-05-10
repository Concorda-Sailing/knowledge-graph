---
node_id: concorda-web::src/components/dashboard/inline-config-create.tsx::InlineConfigCreate
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b5190a55fdb5f965a59cde4e0c374d1b3a9147504786faaad595fe2e9b8a6b1c
status: llm_drafted
---

# InlineConfigCreate

## Purpose

A UI component for creating a new `BoatConfig` via an inline form. It allows users to name a configuration and select/toggle specific equipment positions (like Bow, Pit, or Mast) before submitting. It is a specialized sub-component intended to be used within a dashboard context to avoid the complexity of a full-page configuration flow.

## Invariants

- **`boatId` is required** to target the specific boat being configured.
- **`onCreated` must receive a valid `BoatConfig` object** containing the name and the array of `positions`.
- **`config_type` is hardcoded to `"full"`** during the `profileApi.createBoatConfig` call.
- **Position coordinates are derived from `QUICK_POSITIONS`**; if a position is selected, its `location_x` and `location_y` are pulled from the predefined constants.

## Gotchas

- **Extraction Refactor**: This component was recently extracted from `event-crew-card` in commit `f13ba7c`. Ensure that any logic relying on the previous parent-component context is updated, as it is now a standalone unit.
- **Empty State Guard**: The `handleCreate` function silently returns if the `name` is empty or if no positions are selected (`counts.size === 0`). This prevents empty configurations from being sent to the API but provides no visual feedback to the user.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi` which requires an authenticated session.
- **Side effects**: Upon successful creation, calls `onCreated`, which typically triggers a re-render of the parent dashboard view or the `CrewPositionsCard`.

## External consumers

None known.
