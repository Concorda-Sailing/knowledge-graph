---
node_id: concorda-api::schemas/profile.py::ProfileUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d478d2634bf51db662933b1de1b4c1f8bc8f3784c48fa314d3db6f2351dda9a3
status: current
---

# ProfileUpdate

## Purpose

The schema for self-service profile updates. It defines the structure for partial updates to a user's personal information, including contact details, physical attributes (shirt/shorts sizing), and organizational affiliations. Use this instead of `ProfileRead` when performing `PUT` operations to ensure only intended fields are mutable.

## Invariants

- **All fields are `Optional`** — The schema is designed for partial updates; omitting a field in the request body does not nullify the existing value in the database.
- **Uses `date` objects for temporal fields** — `date_of_birth` and `join_date` must be valid ISO date strings that resolve to Python `date` objects.
- **`meta` is a free-form dict** — The `meta` field allows for arbitrary key-value pairs to support extensible user metadata.

## Gotchas

- **Avoid null-pointer issues in preferences** — Per commit `03a6819`, the `ProfileRead` validator (which handles the output of these updates) must explicitly fill defaults if the input is null or not a dict to prevent crashes in the UI.
- **Sizing fields are string-based** — `shirt_size`, `shorts_waist`, and `shorts_inseam` are `Optional[str]`. Ensure the frontend sends strings rather than numeric types to avoid validation errors.

## Cross-cutting concerns

- **Auth**: Handled by the `PUT /api/profile` router; requires authenticated user context to ensure users can only update their own profile.
- **Side effects**: Updates to `club_affiliations` or `member_category` may affect visibility in the crew finder and roster-related views.

## External consumers

- Web frontend (Profile/Settings pages).
