---
node_id: GET::/api/constants/positions
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ed5bd0f9d0483287f964c0e4b72ae08aec5d1362bedd4edc13783736a61e9ba7
status: llm_drafted
---

# GET /api/constants/positions

## Purpose

Returns the list of available sailing positions used for crew configuration. This endpoint provides the static string options for roles (e.g., Skipper, Crew) to ensure consistency between the boat diagram and user profile settings. It is a read-only endpoint used primarily for populating dropdowns and selection UI.

## Invariants

- **HTTP Method:** `GET`
- **Response Shape:** `list[str]` (a list of strings).
- **Data Source:** Returns the global `POSITIONS` constant defined in the router module.

## Gotchas

- **Static list dependency:** This endpoint returns a static list of strings. If a new position type is required for a specific boat configuration, the `POSITIONS` constant in `concorda-api/routers/constants.py` must be updated.
- **Diagram alignment:** The strings returned here must match the expected keys used in `POSITION_LOCATIONS` to ensure the boat diagram renders the correct position markers.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by the boat crew configuration UI to populate position selection.

## External consumers

- `concorda-web` via `constantsApi.getPositions`.
