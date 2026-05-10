---
node_id: concorda-web::src/components/dashboard/crew-positions-card.tsx::CrewPositionsCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 42cb199336793ec00f05f88b7b7544db766d2defc6891ca3cc2412cdbd07e99c
status: current
---

# CrewPositionsCard

## Purpose

Displays a summary of crew position assignments and provides an interface for owners to assign or clear roles. It visualizes the ratio of accepted crew members to available slots via a badge and allows switching between different `BoatConfig` presets if provided. Use this component when an owner needs to manage the specific roles of crew members within a specific event context.

## Invariants

- **`filledCount` is derived from `acceptedCrew.length`**, not the number of active position assignments.
- **`onAssign` is an asynchronous operation** that must be awaited; the component manages a local `busy` state to prevent concurrent assignment attempts.
- **`onConfigChange` is optional.** The configuration `Select` only renders if `onConfigChange` is present and `configs` contains at least one item.
- **`positionName` can be `undefined`.** Passing `undefined` to `onAssign` acts as a way to clear a person's current position.

## Gotchas

- **The "X/Y" count is decoupled from position names.** Per commit `b4d60c6`, the badge displays the count of accepted invites against open slots regardless of whether a `position_name` is currently assigned to a slot. This ensures the badge remains accurate even if a configuration change invalidates existing position names.
- **`onAssign` must handle the `busy` state.** The component implements a local `setBusy` guard to prevent multiple rapid clicks from triggering multiple API calls.

## Cross-cutting concerns

- **Auth**: Requires owner-level permissions to execute the `onAssign` callback.
- **Side effects**: Changing the configuration via `onConfigChange` will trigger a re-render of the card with the new `positionAssignments` and `slots` relevant to that specific `BoatConfig`.

## External consumers

None known.
