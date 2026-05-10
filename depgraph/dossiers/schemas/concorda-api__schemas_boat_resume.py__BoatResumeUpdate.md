---
node_id: concorda-api::schemas/boat_resume.py::BoatResumeUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 65a7a502da7acff583569dfaad967c08f9d487998ab19f0ea20602bd5165a844
status: current
---

# BoatResumeUpdate

## Purpose

The schema for partial updates to a boat's public-facing resume. It is used by the `PUT /api/profile/boats/{boat_id}/resume` endpoint to allow owners to modify specific attributes of their boat's profile without re-submitting the entire object. It is distinct from `BoatResumeRead` (the full response) and `BoatFinderProfile` (the public view) by allowing all fields to be optional for patch-style updates.

## Invariants

- **All fields are `Optional`** — This allows for partial updates where only the changed fields are sent in the request body.
- **`drinking` and `accepting_crew` use string enums** — These fields expect specific string literals (e.g., `"Yes"`, `"No"`, `"Occasionally"`) rather than booleans.
- **`availability` is a dictionary** — This field must follow the structure expected by the underlying storage to ensure compatibility with the `BoatFinderProfile` view.

## Gotchas

- **`drinking` and `accepting_crew` are strings, not booleans** — Per the source, `drinking` and `accepting_crew` are typed as `Optional[str]`. If a client sends a boolean, the Pydantic validation will fail.
- **Recent expansion of profile fields** — Commit `7aae433` added `banner_url` and `picture_url` to the broader profile context; ensure that any logic consuming this update schema accounts for the fact that `BoatResumeUpdate` does not currently include these media fields, meaning they cannot be updated via this specific endpoint.

## Cross-cutting concerns

- **Auth**: Managed by the `PUT /api/profile/boats/{0}/resume` router.
- **Side effects**: Updates to this schema directly affect the data displayed in the `BoatFinderProfile` and `BoatFinderProfileDetail` views.

## External consumers

- `PUT /api/profile/boats/{0}/resume` (Internal API endpoint).
