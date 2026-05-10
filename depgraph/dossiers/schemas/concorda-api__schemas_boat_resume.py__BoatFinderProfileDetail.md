---
node_id: concorda-api::schemas/boat_resume.py::BoatFinderProfileDetail
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2ff5e1e5b3d5cfe1ec7312dc78424ad59975428950a24974a7f8316eb81898f2
status: llm_drafted
---

# BoatFinderProfileDetail

## Purpose

The detailed view of a boat's profile within the Boat Finder service. It extends the base `BoatFinderProfile` to include specific metadata required for crew matching and social context. Use this schema when the client needs to display full-depth profile details (e.g., on a dedicated detail page) rather than the lightweight summary used in list views.

## Invariants

- **Inherits from `BoatFinderProfile`** — must include all base fields like `owner_first_name` and `owner_last_name`.
- **`viewer_is_crew` is a boolean flag** — used to toggle visibility or context-specific UI elements based on the viewer's relationship to the boat.
- **`typical_crew_complement` is optional** — allows for boats that may not have a fixed number of seats.

## Gotchas

- **Recent expansion of fields** — per commit `7aae433`, this schema was recently updated to support banner/picture URLs and club affiliations. Ensure any new visual elements in the UI are mapped to these specific fields.
- **Dependency on base schema** — because it inherits from `BoatFinderProfile`, any changes to the base class (like field renaming) will propagate here and potentially break the `GET /api/boatfinder/detail/{0}` endpoint.

## Cross-cutting concerns

- **Auth**: None (though the endpoint consuming this, `routers/boatfinder.py:190`, is part of the boat finder flow).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by the boat-finder detail page to render social/crew context.

## External consumers

- `GET /api/boatfinder/detail/{0}` (via `routers/boatfinder.py:190`).
