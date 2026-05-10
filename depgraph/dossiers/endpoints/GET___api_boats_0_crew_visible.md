---
node_id: GET::/api/boats/{0}/crew/visible
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3630b92d9b98e4fab736df7ca9c7af792044895e20eb9cad7e50fe54e6dc360b
status: current
---

# GET /api/boats/{boat_id}/crew/visible

## Purpose

Returns a list of active crew members on a specific boat who have opted into the "crewfinder" feature. This is used to surface a boat's crew to external parties or other users without exposing the full private crew list. It is distinct from the full crew list by filtering for `Person.preferences.crewfinder.opt_in == True` and excluding the requesting user.

## Invariants

- **Requires `require_auth`** — The request must be authenticated.
- **Requires active membership** — The `current_user` must have a membership on the boat with `status == "active"`, otherwise returns a 403.
- **Excludes self** — The `current_user.id` is explicitly filtered out of the results.
- **Returns a list of objects** — Each object contains `person_uuid`, `first_name`, `last_name`, `picture_url`, `role`, and `position`.
- **Gated by resume status** — Only includes people who satisfy the `has_published_resume(person)` check.

## Gotchas

- **Strict opt-in requirement** — Per commit `26b65f8`, this endpoint was specifically updated to include the `crewfinder` opt-in filter. If a user is on the boat but has not opted in, they will be missing from this list.
- **Identity/Privacy mismatch** — The endpoint is designed to be a "public-facing" view of a private crew. If the `has_published_resume` logic is bypassed or changed, it may leak PII that the user intended to keep private.
- **404 vs 403 ambiguity** — The endpoint first checks for boat existence via `_get_boat_or_404`. If the boat doesn't exist, it returns a 404; if the user is not an active crew member, it returns a 403.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and requires the user to have an `"active"` membership status on the boat.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

- `concorda-web` (via `boatApi.getVisibleCrew`)

## Open questions

- Should the `picture_url` be subject to different visibility rules if the user's resume is not published, or is the `has_published_resume` check sufficient?
