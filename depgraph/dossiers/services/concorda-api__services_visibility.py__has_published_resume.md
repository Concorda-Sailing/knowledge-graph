---
node_id: concorda-api::services/visibility.py::has_published_resume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dbeb95c30647db5d115e070d8162fe71b00158a6a733a5bd24b0be4ff3605749
status: llm_drafted
---

# has_published_resume

## Purpose

Determines if a person's PII (name, email, phone, picture) should be visible to a viewer based on their privacy settings. It specifically checks the `crewfinder` opt-in flag within the `person.preferences` dictionary. This is a low-level utility used to gate-keep sensitive data; it is distinct from `peer_can_see_pii`, which handles the higher-level logic of viewer identity and ownership.

## Invariants

- **Input is an optional `Person` object.** If `person` is `None`, the function returns `False`.
- **Relies on nested dictionary structure.** It expects `person.preferences["crewfinder"]["opt_in"]` to be a boolean.
- **Returns a boolean.** The result is strictly `True` (opted-in) or `False` (not opted-in or missing data).
- **Defensive against malformed preferences.** If `preferences` is not a dictionary or the `crewfinder` key is missing/not a dict, it returns `False` rather than raising a `KeyError`.

## Gotchas

- **Recent refactor in `ea4fcb2`** extracted this into a standalone helper to harden the logic and ensure visibility checks are not bypassed by malformed preference schemas.
- **Does not handle administrative bypasses.** Per the docstring, this function only checks the person's opt-in status; it does not know about `event-manager` or `admin` roles. Those roles must be handled by the caller (e.g., via `viewer_is_owner=True` in `peer_can_see_pii`) to ensure they see unfiltered data.

## Cross-cutting concerns

- **Auth**: Used to determine if PII should be masked in API responses.
- **Side effects**: Directly affects the visibility of person data in the `GET /api/boats/{0}/crew/visible` endpoint.

## External consumers

- `GET /api/boats/{0}/crew/visible` (via `routers/boats.py:324`)
