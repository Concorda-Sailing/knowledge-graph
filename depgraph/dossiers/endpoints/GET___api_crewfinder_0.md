---
node_id: GET::/api/crewfinder/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b57134b2702bd12d4c88731cbd6e41ad3e87ace0e1b3ed63501bbfa30e1db68f
status: llm_drafted
---

# GET /api/crewfinder/{resume_id}

## Purpose

Retrieves a specific user's sailing resume for display in the Crew Finder. This endpoint is distinct from a general profile fetch because it enforces strict privacy controls: a user can always see their own resume, but third parties can only access it if the user has explicitly opted into the crew finder via their preferences.

## Invariants

- **Auth Required** — Uses `require_auth` to ensure the requester is a logged-in user.
- **Privacy Guard** — If the `current_user.id` is not the owner of the `resume_id`, the function checks `person.preferences.get("crewfinder", {}).get("opt_in")`.
- **404 vs 403** — To prevent leaking the existence of a resume to unauthorized users, the API returns a `404 Not Found` instead of a `403 Forbidden` if the user has not opted into the crew finder.
- **Return Shape** — Returns a `SailingResumeRead` object, which includes nested data like `notable_races`, `certifications`, and `race_areas`.

## Gotchas

- **Security/PII Leakage** — Per commit `33a37a3`, this endpoint was specifically hardened to close privilege gaps. Previously, a user could guess a `resume_id` to view private data; the current implementation requires the `opt_in` flag to be true for non-owners to prevent P/PII exposure.
- **Implicit Dependency on Person Preferences** — The visibility of a resume is tied to the `person.preferences` dictionary. If the `person` object is missing or the `preferences` key is not structured correctly, the lookup may fail or default to a non-opted-in state.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth`.
- **Side effects**: Changes to this resume (via `POST` or `PUT` on the same router) affect the visibility of the user in the "Crew Finder" directory and boat owner searches.

## External consumers

None known.
