---
node_id: concorda-api::schemas/event_registration.py::EventRegistrationRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3f8b4f876b433599a2ce99b156a7302710f63d450a1d5c0e941f986a4e803285
status: llm_drafted
---

# EventRegistrationRead

## Purpose

The read-only representation of an event registration used for listing and retrieving registration data. It is distinct from `EventRegistrationConfirmation` (which includes pricing/ticket details for the user) and `MyEventRegistration` (which includes event-specific metadata like location and date). Use this schema when building endpoints that list registrations for an event or when returning a general registration view where pricing and ticket names are not required.

## Invariants

- **`id` and `event_id` are required strings.**
- **`created` must be a valid datetime object.**
- **`status` is a required string.**
- **`product_id` is a required string.**
- **`comment` is an optional string.**

## Gotchas

- **Part of the new registration system.** Per commit `6405007`, this schema is part of the foundational rollout for the registration and payment system; ensure any changes to the registration flow are reflected in both this and the `Confirmation` schemas to avoid mismatching the public view.

## Cross-cutting concerns

- **Auth**: Used by `GET::/api/events/{0}/registrations` (requires event owner/admin permissions).
- **Side effects**: Changes to this schema will affect the response shape of the registration list view in the event management dashboard.

## External consumers

- None known.
