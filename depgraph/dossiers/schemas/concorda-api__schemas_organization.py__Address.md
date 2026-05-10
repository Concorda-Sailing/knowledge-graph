---
node_id: concorda-api::schemas/organization.py::Address
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5442cdc3cd8dd5de84c611381f393fc36ab8a2965e76358bbdbb3dd9a683fe62
status: llm_drafted
---

# Address

## Purpose

The `Address` model provides a structured representation of a physical location for an Organization. It is a nested Pydantic model used primarily within `OrganizationCreate` to ensure type-safe ingestion of location data. While `OrganizationCreate` uses the typed `Address` model, the `OrganizationRead` schema uses a `dict` for the address field to facilitate easier serialization and compatibility with the database layer.

## Invariants

- **All fields are optional.** `street`, `city`, `state`, and `zip` are all `Optional[str] = None`, allowing for partial address data.
- **Used as a nested object.** In the creation flow, it must be passed as a dictionary matching the `Address` schema structure.
- **Type-safe in creation, dict-based in reading.** When consuming `OrganizationRead`, the address is treated as a `dict` rather than the `Address` class instance.

## Gotchas

- **Schema mismatch between Create and Read.** Per the source, `OrganizationCreate` expects the `Address` class, but `OrganizationRead` expects `Optional[dict]`. Any logic attempting to perform type-specific methods on the address field when reading from the API will fail, as it is cast to a dictionary.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
