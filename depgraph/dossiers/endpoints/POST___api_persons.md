---
node_id: POST::/api/persons
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b2a1fdbb34f076e872e81320d102e6a898c8c190ac43d8bc45030d5aa699d1ba
status: llm_drafted
---

# POST /api/persons

## Purpose

Creates a new person record in the system. This endpoint is used during user onboarding and registration flows to establish a `Person` identity, which is a prerequisite for assigning roles or managing crew memberships. It is distinct from the `PUT` method in that it handles the initial instantiation of the `preferences` dictionary.

## Invariants

- **Requires `_require_admin` dependency** — Only users with administrative privileges can create new persons.
- **Input must be `PersonCreate`** — The payload must conform to the `PersonCreate` schema.
- **Email uniqueness is enforced** — If a person with the provided email already exists, the API returns a `400 Bad Request`.
- **`preferences` initialization** — If the input payload does not contain a `preferences` key, the method defaults to an empty dictionary `{}` to prevent null pointer errors in the frontend.
- **Returns `PersonRead`** — The response is the fully instantiated `Person` object, including the generated ID.

## Gotchas

- **PII/Privilege Gap** — Per commit `33a37a3`, this endpoint and its associated models were part of a security hardening effort to close PII and privilege gaps in roles and directory access. Ensure any changes to the `Person` model do not inadvertently expose sensitive fields to non-admin users.
- **Preference Nullability** — The logic in lines 114-118 explicitly handles the `preferences` key. If a developer removes this block, the database might receive a null value where the frontend expects an object, potentially breaking the UI.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` dependency.
- **Websocket**: `update_person` (the sibling `PUT` method) emits the `PERSON_UPDATED` event.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: Changes to person data via the sibling `PUT` method trigger updates to any UI components listening for `PERSON_UPDATED`.

## External consumers

None known.
