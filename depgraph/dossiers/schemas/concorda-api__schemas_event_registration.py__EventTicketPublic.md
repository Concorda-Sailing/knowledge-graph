---
node_id: concorda-api::schemas/event_registration.py::EventTicketPublic
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 20dde01aa0fac9d0a629138d4eac8ffc1efdc505b2b4a14e10a512e9d6f5e284
status: llm_drafted
---

# EventTicketPublic

## Purpose

The `EventTicketPublic` schema defines the structure for the public-facing view of an event ticket. It is distinct from `EventRegistrationCreate` or `MyEventRegistration` because it focuses strictly on the metadata required to display ticket availability and pricing to a potential registrant, rather than the user's personal registration details. Use this schema when building endpoints that list available tickets for an event (e.g., the ticket selection step).

## Invariants

- **`id` and `slug` are required strings.** The `id` refers to the unique ticket type, while the `slug` identifies the parent event.
- **`price` is a `Decimal`.** This ensures precision for financial calculations and prevents floating-point errors in the UI.
- **`available` is a boolean flag.** This indicates whether the ticket type is currently open for registration.
- **`from_attributes = True` is required.** This allows the schema to be instantiated directly from SQLAlchemy/ORM models during the serialization of the `GET /api/events/slug/{slug}/tickets` response.

## Gotchas

- **Part of the initial registration system rollout.** Per commit `6405007`, this schema is part of the new event management and registration system; ensure any changes to the `Decimal` or `Optional` types are reflected in the frontend's type definitions to avoid serialization mismatches.

## Cross-cutting concerns

- **Auth**: None. This is a public-facing schema used for browsing available tickets.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `GET /api/events/slug/{slug}/tickets` to populate the ticket selection UI.

## External consumers

- `GET /api/events/slug/{slug}/tickets` (Internal API endpoint).
