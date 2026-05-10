---
node_id: concorda-api::schemas/event_registration.py::MyEventRegistration
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: db66a10967cd22f1347f5401767422cb2098eb1aaf0df28d96d34c0c2514a3c3
status: llm_drafted
---

# MyEventRegistration

## Purpose

Defines the data structure for a user's personal event registration. It is a read-optimized schema used to present a summary of a user's participation in an event, combining event-level metadata (name, date, location) with transaction-level data (ticket price, transaction ID). Use this when building profile views or registration history lists rather than the core `Event` or `Product` schemas.

## Invariants

- **`id` is a string.** This refers to the registration record ID, not the event ID.
- **`event_date` is a required datetime.** The schema assumes the event is a fixed point in time.
- **`ticket_price` uses `Decimal`.** This ensures precision for financial data and avoids floating-point errors during serialization.
- **`event_slug` is optional.** This allows for generic event displays where a URL-friendly slug might not be available.

## Gotchas

- **Introduced in commit `6405007`** as part of the massive registration system rollout. This schema is relatively new and represents the current standard for "user-facing registration data."

## Cross-cutting concerns

- **Auth**: Dependent of `GET /api/profile/event-registrations`, which requires user authentication to ensure users only see their own registrations.
- **Side effects**: Changes to the underlying registration logic or product pricing will propagate to the user's profile view via this schema.

## External consumers

- `GET /api/profile/event-registrations` (Internal API endpoint).
