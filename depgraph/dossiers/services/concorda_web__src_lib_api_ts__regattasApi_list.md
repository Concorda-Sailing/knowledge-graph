---
node_id: concorda-web::src/lib/api.ts::regattasApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bc340d72ce17e112ca575d51e2db2c5fd073f685f69f19a89898c29583ee184e
status: llm_drafted
---

# regattasApi.list

## Purpose

Fetches a list of regattas from the backend, supporting optional filtering by `region` or `regatta_type`. This is the primary method for populating regatta-specific views and lists. It is distinct from `eventsApi.addRegattas` (which is a write operation) and `socialsApi.list` (which is a broader, non-filtered category fetch).

## Invariants

- **Returns `Event[]`** — the response is a collection of event objects.
- **Query parameters are optional** — if `params` is undefined, the request is sent to the base `/api/events/regattas/` endpoint without a query string.
- **Uses `fetchApi`** — unlike the `analyticsApi` methods, this does not explicitly call `fetchApiAuthenticated`, implying it relies on the standard unauthenticated or session-based `fetchApi` behavior for the events endpoint.

## Gotchas

- **Filtering logic is sensitive to parameter presence** — the `query` string is only appended if `params.region` or `params.regatta_type` are truthy.
- **Recent regatta UI changes** — per commit `b67d359`, the regatta display logic is tied to per-race toggles for "Accepting-Crew" badges; ensure that any changes to the returned `Event` shape do not break the badge rendering in the UI.

## Cross-cutting concerns

- **Auth**: none (uses standard `fetchApi`).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: The results of this call are used to drive the "Accepting-Crew" status and badge visibility on regatta detail views and schedule cards (per commit `2d6b8a7`).

## External consumers

None known.
