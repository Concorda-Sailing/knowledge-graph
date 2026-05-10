---
node_id: concorda-web::src/lib/api.ts::regattaApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a7d7e495037bf638ccfe42ca6437d13bec7654de581b1d8a986e001d3d11af85
status: current
---

# regattaApi.update

## Purpose

The `regattaApi.update` method performs a partial update on an existing regatta (Sailing Event) via a `PUT` request. It is used to modify specific fields of a `RegattaDetail` object, such as the boat configuration, crew status, or event timing. Use this instead of `create` when modifying an existing event, and ensure the `id` matches the specific regatta being edited.

## Invariants

- **HTTP Method is `PUT`** — Performs a partial update on the resource at `/api/regattas/{id}`.
- **Requires a valid `id`** — The first argument must be the unique identifier for the regatta.
- **Input is a `Partial<RegattaDetail>`** — Only the fields provided in the `data` object are sent to the server.
- **Returns `RegattaDetail`** — The method returns the full, updated state of the regatta object.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to authorize the request.

## Gotchas

- **`boat_config_id` vs. `boat_uuid`** — Per commit `bf15808`, the API expects the stored `boat_config_id` for consistency; do not attempt to shape-match or pass raw boat objects if you are updating the link to a boat.
- **Status/Badge dependency** — Per commit `b4d60c6`, updates to the regatta (like changing the `accept_crew_requests` toggle) directly drive the "Accepting-Crew" badge visibility on the schedule card.
- **Manual status updates** — Per commit `b67d359`, the logic for the "Accepting-Crew" badge is driven by the per-race toggle; ensure the `data` payload correctly reflects the intended state of the `accept_crew_requests` boolean.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires bearer token).
- **Side effects**: Updates to this method affect the "Accepting-Crew" badge and the "X accepted of Y" count logic on the schedule detail page and schedule cards.

## External consumers

- `RaceEditorContent` in `src/app/members/admin/events/races/[id]/page.tsx`.

## Open questions

- Should the `update` method be strictly typed to `SailingEventUpdate` instead of `Partial<RegattaDetail>` to prevent accidental field injection that the API might not support?
