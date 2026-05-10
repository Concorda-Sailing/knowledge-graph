---
node_id: GET::/api/events/slug/{0}/my-registration
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 64f45083f9cbf68de43fdc4cda8a517ad5667b9ade9213cbf170b0a7bbd61e8b
status: llm_drafted
---

# GET /api/events/slug/{slug}/my-registration

## Purpose

Retrieves the confirmed registration details for the currently authenticated user for a specific event, identified by its slug. It is distinct from the `confirmation` endpoint, which allows lookup via a specific registration ID and provides broader access (including admin/owner overrides). Use this endpoint when the UI needs to display a user's own personal event schedule or registration status without requiring a specific registration ID.

## Invariants

- **Requires Authentication** — Uses `require_auth` to ensure a valid `current_user` is present.
- **Returns `list[EventRegistrationConfirmation]`** — The response is an array of objects containing `id`, `first_name`, `email`, `status`, `created`, `ticket_name`, `ticket_price`, and `transaction_id`.
- **Filters by "Confirmed" status** — Only returns registrations where the status is explicitly `"Confirmed"`.
- **Requires a valid Event Slug** — If the slug does not match an existing event, the API returns a `404 Not Found`.

## Gotchas

- **Slug collision risk** — Per commit `4fd165d`, the system dropped slugs for personal events to avoid global `UNIQUE` constraint collisions in the database.
- **Strict status requirement** — If a user is registered but the status is not `"Confirmed"`, the returned list will be empty even if the record exists.
- **Product lookup dependency** — The `ticket_name` and `ticket_price` are derived from the associated `Product` record; if the product is missing or deleted, the endpoint defaults to `"Unknown"` and `0` respectively.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` (authenticated user).
- **Side effects**: Used by the `eventsApi.getMyRegistration` client in `concorda-web` to populate user-specific event views.

## External consumers

- `concorda-web` (via `eventsApi.getMyRegistration`)
