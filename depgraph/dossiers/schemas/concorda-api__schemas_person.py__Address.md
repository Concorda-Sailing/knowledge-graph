---
node_id: concorda-api::schemas/person.py::Address
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5442cdc3cd8dd5de84c611381f393fc36ab8a2965e76358bbdbb3dd9a683fe62
status: llm_drafted
---

# Address

## Purpose

The `Address` schema provides a standardized structure for physical location data within the `Person` model. It is a sub-component used primarily by `PersonCreate` to encapsulate mailing or physical location details. Use this instead of raw strings when a person's location requires structured fields (street, city, state, zip) to support future mailing or geocoding logic.

## Invariants

- **All fields are optional.** `street`, `city`, `state`, and `zip` can all be `None` or omitted without triggering a validation error.
- **Type is `Optional[str]`.** All fields must be strings or null; passing non-string types will fail Pydantic validation.
- **Used as a nested model.** In `PersonCreate`, it is assigned to the `mailing_address` field.

## Gotchas

- **Implicitly null-friendly.** Because all fields are `Optional`, a client can send an empty object `{}` or a partially filled object without breaking the `PersonCreate` schema.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: Used by `PersonCreate` to establish the physical identity of a user, which may impact downstream mailing or registration logic.

## External consumers

- None known.
