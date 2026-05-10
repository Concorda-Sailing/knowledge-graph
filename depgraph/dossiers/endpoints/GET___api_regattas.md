---
node_id: GET::/api/regattas
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 84471f6f87b4a5b73bc5ba02a5f243eef9b9eb9c5148e71140096e7db1d389fb
status: llm_drafted
---

# GET /api/regattas

## Purpose

Provides a list of all regattas, optionally filtered by `region_uuid` or `course_type`. It is the primary endpoint for populating regatta directories and schedule views. Unlike the single-object fetchers, this method is responsible for aggregating `match_counts` (boats total, looking, and available) for every regatta in the list to provide a high-level overview of participation density.

## Invariants

- **Returns a list of `RegattaRead` objects.** Each object includes embedded `match_counts` and `organizing_authorities`.
- **Ordering is chronological.** Results are always ordered by `Regatta.start.desc()`.
- **Filtering is optional.** If `region_uuid` or `course_type` are not provided, the full list is returned.
- **Data enrichment via `_attach_counts`.** The response shape is dependent on the successful execution of the internal `_attach_counts` helper.

## Gotchas

- **Performance overhead of `_attach_counts`.** Because this endpoint embeds match counts for every regatta in the list, it is more computationally expensive than a standard CRUD list. Large result sets may see latency increases as the number of regattas grows.
- **`match_counts` dependency.** Per commit `e1c7e44`, the schema relies on a specific aggregation logic to show `boats_total`, `boats_looking`, and `crew_available`. Changes to the underlying `counts` logic will directly impact the visibility of participation metrics in the UI.

## Cross-cutting concerns

- **Auth**: None (Publicly accessible via `GET`).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by the regatta directory and schedule views to display participation density.

## External consumers

- `concorda-web` (via `regattaApi.list`)
- `concorda-test` (via `ApiClient.listRegattas`)
