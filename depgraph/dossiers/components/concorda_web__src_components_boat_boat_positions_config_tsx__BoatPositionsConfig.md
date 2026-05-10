---
node_id: concorda-web::src/components/boat/boat-positions-config.tsx::BoatPositionsConfig
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 91a31ba3a3e5f835efdb4e2e77ce45fe5ec68bb62d1cb252f0a106cddcc5b8bc
status: current
---

# BoatPositionsConfig

## Purpose

Manages the configuration of crew positions and counts for a specific boat. It provides an interface for boat owners to create, delete, and set default configurations from a set of predefined `PRESETS`. This component is used to ensure that a boat's crew requirements (e.g., number of helmsmen, tacticians, etc.) are standardized and easily configurable.

## Invariants

- **Ownership required for mutation.** The `isOwner` prop must be `true` for the component to trigger `seedDefaultConfigs`, `handleDelete`, or `handleSetDefault`.
- **Automatic seeding.** If `isOwner` is true and `listBoatConfigs` returns an empty array, the component automatically executes `seedDefaultConfigs` to populate the boat with default `PRESETS`.
- **Single Default Rule.** When `handleSetDefault` is called, the component updates the API and locally resets all other configurations to `is_default: false` for that boat.
- **Data Shape.** The `positions` field in the API call is generated via `positionsToApi(counts)`, converting the local Map of names and counts into the expected API format.

## Gotchas

- **Seeding side effects.** The `seedDefaultConfigs` function uses a `try/catch` block to "skip duplicates" (line 93). This is a silent failure mode intended to prevent the UI from breaking if a user attempts to re-seed a boat that already has configurations.
- **Mobile Reflow.** Per commit `189dcf9`, this component requires careful attention to layout; the positions configuration must support a single-column reflow and stacked actions for mobile-friendly interaction.
- **Dashboard Integration.** Per commit `76ad44e`, this component is part of the "Dashboard overhaul" and is expected to work inline with other boat management tools.

## Cross-cutting concerns

- **Auth**: Requires `isOwner` prop to be true for all write operations (`createBoatConfig`, `deleteBoatConfig`, `updateBoatConfig`).
- **Audit**: Y (Writes to `profileApi` which logs configuration changes).
- **Side effects**: Rebuilds the boat's configuration state; affects how the boat's crew requirements are displayed in the boat-finder and profile views.

## External consumers

None known.
