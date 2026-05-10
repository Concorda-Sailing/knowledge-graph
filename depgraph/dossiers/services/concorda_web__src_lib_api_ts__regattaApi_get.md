---
node_id: concorda-web::src/lib/api.ts::regattaApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 90dc28ae94ad03725e0fd03a3b34e35153603e56902f96adba6f39d8a70a30f9
status: llm_drafted
---

# regattaApi.get

## Purpose

Provides a single-resource interface for managing regattas. It handles fetching individual regatta details, listing all regattas, and performing CRUD operations (create, update, delete). Use this when you need to interact with the regatta entity directly, as opposed to `seriesApi` which manages the higher-level grouping of races.

## Invariants

- **Uses `fetchApiAuthenticated`** — all calls require a valid bearer token and follow the authenticated-request pattern.
- **`get(id)` returns `RegattaDetail`** — the return type is a single object representing the specific regatta.
- **`create` and `update` use `Partial<RegattaDetail>`** — the API accepts partial payloads for updates, allowing for granular field updates.
- **`delete` returns `void`** — successful deletion results in an empty response body.

## Gotchas

- **`checkDuplicates` requires specific payload structure** — unlike other methods that take an `id`, this performs a POST to `/api/regattas/check-duplicates` with an array of items.
- **`accept_crew_requests` toggle drives UI state** — per commit `b67d359`, the "Accepting-Crew" badge visibility is driven by this specific toggle within the regatta detail.
- **`boat_config_id` is the source of truth for counts** — per commit `bf15808`, the UI relies on the stored `boat_config_id` to ensure the schedule card displays the correct configuration-aware counts.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Updates to regatta data (via `create` or `update`) will affect the "Accepting-Crew" badge status and the `RegattaDetail` view in the Schedule and Race Editor.

## External consumers

- `RaceEditorContent` in the admin/events/races path.
- `ScheduleEventDetail` in the members/schedule path.
