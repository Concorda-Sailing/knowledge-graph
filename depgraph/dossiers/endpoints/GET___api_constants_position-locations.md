---
node_id: GET::/api/constants/position-locations
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 055763e6f776fa8fe7bf385501a5830c71806401ef143fdf7089de9e6a0d0226
status: current
---

# GET /api/constants/position-locations

## Purpose

Returns the default position locations used for rendering the boat diagram in the UI. This is a static configuration endpoint used to ensure the frontend has a consistent set of coordinate/label identifiers for crew positions. It is distinct from `/api/boat-config-templates`, which provides the actual crew configuration data; this endpoint only provides the spatial/positional metadata.

## Invariants

- **Returns a static list of position objects.** The response shape is determined by the `POSITION_LOCATIONS` constant in the backend.
- **HTTP Method is GET.**
- **No parameters required.** The endpoint does not accept query parameters or path variables.

## Gotchas

- **Dependency on diagram support.** Per commit `74b26e5`, this endpoint was introduced to support "boat crew configurations with position diagram support." Changes to the structure of this return value will directly impact the rendering of the position diagram in the frontend.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: affects the rendering of the boat diagram/crew configuration UI.

## External consumers

- concorda-web (used for boat diagram position rendering).
