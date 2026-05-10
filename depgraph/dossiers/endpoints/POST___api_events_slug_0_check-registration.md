---
node_id: POST::/api/events/slug/{0}/check-registration
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 679dfad02bc424fa2d3ac9d5ffd6c91fa983ef453cbff42efedbec655734b50c
status: llm_drafted
---

# POST /api/events/slug/{slug}/check-registration

## Purpose

Provides a pre-flight validation check for event registration before a user attempts to commit a payment or registration. It verifies that the event exists, the registration deadline has not passed, the requested products (tickets) are active and have sufficient remaining quantity, and that the specific email address is not already registered for the event. This is used to provide immediate feedback in the UI to prevent failed checkout attempts.

## Invariants

- **HTTP Method**: `POST`.
- **Path Parameter**: Requires a valid `slug` for the event.
- **Request Body**: Must contain `product_ids` (list of strings) and `email` (string).
- **Return Shape**: Returns a `RegistrationCheckResponse` containing `ok: bool` and an optional `error: str`.
- **Deadline Check**: Uses `datetime.now(timezone.utc)` to compare against `event.registration_deadline`.
- **Product Validation**: A product is only valid if it belongs to the event and `is_active` is `True`.

## Gotchas

- **Registration Status Dependency**: The check for existing registrations (line 1550) and product quantity (line 1540) specifically filters for `status == "Confirmed"`. If a registration is in a different state (e.g., "Pending"), this endpoint may return `ok: True` even if the user is technically already in the system.
- **Slug Collision Risk**: Per commit `4fd165d`, the system uses slugs for events, but there is a known tension regarding global `UNIQUE` collisions for personal events. Ensure the `slug` passed here is the one intended for public-facing event identification.

## Cross-cutting concerns

- **Auth**: None (this is a pre-auth check used to validate intent before the user is forced to sign in/pay).
- **Rate limit**: none.
- **Side effects**: This is a read-only check; it does not mutate the database or trigger any registration-related side effects.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.checkRegistration` (used by the registration/checkout flow).
