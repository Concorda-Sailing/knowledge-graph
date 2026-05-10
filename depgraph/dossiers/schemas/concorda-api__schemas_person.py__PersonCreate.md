---
node_id: concorda-api::schemas/person.py::PersonCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 06a4385d0a2b0bdfa2872e38df9b9c4741a692edc5c0fdfb8b55dba4c39af6fd
status: current
---

# PersonCreate

## Purpose

The input schema for creating a new person record. It defines the required and optional fields for person-centric data, including contact information, physical attributes (shirt size, shorts dimensions), and organizational affiliations. Use this instead of `PersonRead` when performing `POST` or `PUT` operations to ensure only creation-appropriate fields are sent to the API.

## Invariants

- **Requires core identity fields.** `first_name`, `last_name`, and `email` are mandatory for a valid instantiation.
- **Optionality of contact/physical data.** Fields like `picture_url`, `phone_number`, `mailing_address`, and `shirt_size` are all `Optional` to allow for partial profile completion.
- **`organization_ids` is a list of strings.** It expects a list of UUIDs/IDs for linking the person to specific organizations.
- **Follows the `PersonRead` structure for compatibility.** Most fields match the read-side schema to allow for easy round-tripping of data from the UI to the API.

## Gotchas

- **`club_affiliations` and `shorts_waist/inseam` are recent additions.** Per commit `7aae433`, these fields were added to support the "crew finder detail pages" and "club affiliations" features; ensure any migration or seed scripts account for these new fields.
- **`picture_url` and `banner/picture URLs` dependency.** Commit `7aae433` indicates that picture URLs are now part of the boat finder/crew detail context; ensure URLs provided here are valid and accessible to the frontend.

## Cross-cutting concerns

- **Auth**: Handled by the `POST /api/persons` and `PUT /api/persons/{0}` routers.
- **Side effects**: Updates to this schema (via `PUT`) affect the "crew finder detail pages" and "club affiliations" displays.

## External consumers

- `POST /api/persons` (routers/persons.py)
- `PUT /api/persons/{0}` (routers/persons.py)
