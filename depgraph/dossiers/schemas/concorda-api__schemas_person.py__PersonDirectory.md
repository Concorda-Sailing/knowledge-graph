---
node_id: concorda-api::schemas/person.py::PersonDirectory
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4e5dfaf7acc1601c0066dc2c2f7b7e834be9e058ec506109b842cb91beee0682
status: current
---

# PersonDirectory

## Purpose

The `PersonDirectory` schema defines the public-facing view of a member within the API. It is a subset of the full user profile, designed specifically for directory lookups where certain sensitive fields are omitted. Use this model when building features that display a list of people (like crew or event rosters) rather than a private profile view.

## Invariants

- **`from_attributes = True`** — The model is designed to be instantiated directly from ORM objects (e.g., SQLAlchemy models).
- **`has_boat_management` is a computed field** — It indicates if the person holds a product granting management rights; this is determined at lookup time to inform the UI.
- **`id` is a required string** — Every entry must have a unique identifier.
- **`organization_ids` is an optional list of strings** — Allows for multi-org membership visibility in the directory.

## Gotchas

- **`has_boat_management` is a recent addition** — Per commit `8f94a94`, this field was added to surface boat-management eligibility. This is used by the inviting UI to show a "gate" (warning/prompt) before a user sends an invite to a potential co-owner.
- **Visual assets are optional** — `picture_url` and `banner_url` are `Optional[str]`. If these are missing, the frontend must handle the absence of an image to avoid broken UI elements.

## Cross-cutting concerns

- **Auth**: This schema is used by `GET /api/persons/directory`, which is a public-facing endpoint for "opted-in" members.
- **Side effects**: The `has_boat_management` field directly impacts the "upgrade-prompt nudge" in the inviting UI (per commit `8f94a94`).

## External consumers

- `GET /api/persons/directory` (via `routers/persons.py`)
