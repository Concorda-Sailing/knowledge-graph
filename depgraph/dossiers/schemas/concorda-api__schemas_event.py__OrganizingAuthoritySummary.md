---
node_id: concorda-api::schemas/event.py::OrganizingAuthoritySummary
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1a22f7292a045de23ca070bd4e20be5c7fe0719011c0d5a236b66c07083b5fe2
status: llm_drafted
---

# OrganizingAuthoritySummary

## Purpose

A lightweight data transfer object (DTO) used to represent a high-level summary of an organization. It is specifically designed to be embedded within the `organizing_authorities` list in the `EventRead` schema, providing just enough metadata (ID, name, slug, and abbreviation) to identify the authority without the overhead of a full organization object.

## Invariants

- **`id` is a required string.** It serves as the primary identifier for the authority.
- **`name` is a required string.** This is the human-readable name used for display in event lists.
- **`slug` and `abbreviation` are optional.** They may be `None` if the organization has not yet defined these specific identifiers.
- **`region` is optional.** It allows for geographic grouping of the authority.

## Gotchas

- **`abbreviation` is a relatively new field.** Per commit `bbe1627`, this field was added to support the "organization abbreviation column" in the UI. Ensure any consumer of this schema is prepared to handle the presence or absence of this field.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `EventRead` to populate the authority list in event-related views.

## External consumers

None known.
