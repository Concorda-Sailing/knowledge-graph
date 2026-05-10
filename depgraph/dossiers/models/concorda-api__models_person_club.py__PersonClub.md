---
node_id: concorda-api::models/person_club.py::PersonClub
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 503fbca0f6ff30a6687c21f0ae00f7932c713b408a4e251f10a57b26dc59fd79
status: llm_drafted
---

# PersonClub

## Purpose

Defines the many-to-many relationship between a person and an organization. It acts as a join table that tracks a user's membership status, specific role, and the date they joined a specific club/organization. Use this model when querying a user's affiliations or verifying if a person has permission to act on behalf of an organization.

## Invariants

- **`person_uuid` and `organization_uuid` are required.** Both must be valid UUID strings (36 characters) to maintain referential integrity.
- **`role` is nullable.** A user can be a member of a club without an explicit role assigned.
- **`joined_date` uses the `Date` type.** This field stores the calendar date of joining, not a full timestamp.
- **Inherits from `BaseModel`.** This ensures the record is automatically typed as a `"PersonClub"` in the system's internal type-tracking logic.

## Gotchas

- **Schema redesign impact.** Per commit `ee82e42`, this model is part of a recent structural overhaul involving new relationship tables and data migrations; ensure any new queries to this table account for the updated relationship-based architecture.

## Cross-cutting concerns

- **Auth**: Used to verify organization-level permissions (e.g., determining if a user has a "role" sufficient to access admin endpoints).
- **Audit**: N/A
- **Side effects**: Changes to this table (adding/removing a person from a club) may affect the visibility of organization-specific assets in the UI.

## External consumers

None known.
