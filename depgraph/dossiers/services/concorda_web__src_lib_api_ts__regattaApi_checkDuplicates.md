---
node_id: concorda-web::src/lib/api.ts::regattaApi.checkDuplicates
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7558f7a60e585f441325e0b7170e44c1332dded3139c65d55e1172c70f18a2da
status: llm_drafted
---

# regattaApi.checkDuplicates

## Purpose

The `checkDuplicates` method is a validation helper used during bulk regatta imports to identify potential naming or scheduling collisions. It accepts an array of items (name and optional start time) and returns a list of existing matches found in the database. Use this method instead of individual `get` calls when a user is uploading a file or a list of events to prevent redundant API round-trips and to provide immediate feedback on potential conflicts.

## Invariants

- **HTTP Method is `POST`** — despite being a "check" (read-only intent), it requires a POST to send the `items` array in the body.
- **Requires `fetchApiAuthenticated`** — the call must include a valid bearer token to pass the API gateway.
- **Input shape is an array of objects** — each object must contain at least `name` and can optionally include `start`.
- **Return shape is a list of matches** — each match object contains `name`, `start`, `match_id`, `match_name`, `match_start`, and `match_type`.

## Gotchas

- **Implicit dependency on `match_type`** — the response relies on the backend's ability to categorize the collision; ensure the UI handles the `match_type` field correctly to show if it's a name collision or a time collision.
- **Bulk-processing requirement** — the method is designed for the `ImportRacesContent` component in the admin dashboard; do not attempt to use this for single-event validation if the backend expects a single object rather than an array.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires bearer token).
- **Side effects**: Used by `ImportRacesContent` in the admin event import flow to pre-validate data before final submission.

## External consumers

- `concorda-web::src/app/members/admin/events/import/page.tsx` (ImportRacesContent)

## Open questions

- Is there a maximum length for the `items` array? The backend may have a limit on payload size for the `/api/regattas/check-duplicates` endpoint that isn't explicitly typed in the frontend.
