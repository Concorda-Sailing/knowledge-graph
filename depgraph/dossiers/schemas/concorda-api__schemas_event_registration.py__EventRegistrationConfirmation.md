---
node_id: concorda-api::schemas/event_registration.py::EventRegistrationConfirmation
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 190ad8a3b51d207a982d3dde926ecd4d2402c1c0978401217a013a8e4af7e644
status: llm_drafted
---

# EventRegistrationConfirmation

## Purpose

The public-facing schema for an event registration confirmation. It provides a read-only view of a registration, distinct from `MyEventRegistration` which includes event-specific metadata like `event_location` and `event_slug`. Use this when returning data to a user who needs to verify their ticket details (price, name, and status) without needing the full event context.

## Invariants

- **`from_attributes = True`** — The schema is designed to be instantiated directly from ORM models (e.g., SQLAlchemy objects).
- **`id` is a string.**
- **`ticket_price` is a `Decimal`.**
- **`created` is a `datetime` object.**
- **`transaction_id` is optional.**

## Gotchas

- **New schema dependency.** This model was introduced in commit `6405007` as part of the registration system rollout; ensure any new registration-related endpoints use this rather than returning the raw database model to avoid leaking internal event fields.

## Cross-cutting concerns

- **Auth**: Used by `GET /api/events/slug/{0}/confirmation` and `GET /api/events/slug/{0}/my-registration`.
- **Side effects**: Changes to registration status or price in the database will be reflected in the output of these endpoints.

## External consumers

- Web frontend (via `GET /api/events/slug/{0}/confirmation`).
