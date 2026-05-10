---
node_id: concorda-api::schemas/event_registration.py::EventRegistrationCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 45867cf4f1f0e0739f46195348cf2b962b5b9a05e0c69ad75485fecd4bac1cda
status: current
---

# EventRegistrationCreate

## Purpose

Defines the input schema for creating a new event registration. This model captures the essential user and transaction data required to link a person to a specific event product. It is distinct from `EventRegistrationRead` or `MyEventRegistration`, which include server-generated fields like `id`, `status`, and `created`.

## Invariants

- **`product_id` is required.** This links the registration to the specific temporal product/event being purchased.
- **`first_name` and `last_name` are mandatory.** The registration cannot be processed without these identity fields.
- **`email` is a required string.** This serves as the primary contact identifier for the registration.
- **`transaction_id` and `comment` are optional.** These are used for external payment tracking and user notes respectively.

## Gotchas

- **Part of the initial registration system rollout.** Per commit `6405007`, this schema is part of the new event management and registration system; ensure any changes to the registration flow are reflected in the downstream `POST /api/events/slug/{0}/register` endpoint.

## Cross-cutting concerns

- **Auth**: Requires authentication via the registration endpoint.
- **Audit**: N/A
- **Side effects**: Successful registration via this schema triggers the creation of a registration record which is visible in the `MyEventRegistration` view.

## External consumers

- `POST /api/events/slug/{0}/register` (via `routers/events.py:1659`)
