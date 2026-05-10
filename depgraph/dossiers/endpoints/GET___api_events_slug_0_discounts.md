---
node_id: GET::/api/events/slug/{0}/discounts
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a22f29354e95de36aa8a98c5e54497ee1a5e4292357b4ff5dab1d797ca969b5
status: current
---

# GET /api/events/slug/{slug}/discounts

## Purpose

Retrieves a list of active discount codes associated with a specific event. This is a public-facing endpoint used to show available promotions to users before they reach the checkout/registration phase. It is distinct from registration-check endpoints as it does not require user identity or product selection, only the event slug.

## Invariants

- **Method/Path**: `GET /api/events/slug/{slug}/discounts`.
- **Input**: Requires a valid `slug` string representing the event.
- **Return Shape**: Returns a list of `EventDiscountPublic` objects.
- **Filter Logic**: Only returns discounts where `is_active == True` for the specific `event_id` associated with the slug.
- **Error State**: Returns a `404` if the event slug does not match any existing event in the database.

## Gotchas

- **Slug Uniqueness**: Per commit `4fd165d`, slugs for personal events were dropped to avoid global `UNIQUE` collisions. Ensure the slug provided is the public-facing identifier, not an internal ID.
- **Public Visibility**: This endpoint is designed for public consumption; it does not require an authentication token, but it only returns the `is_active` subset of discounts.

## Cross-cutting concerns

- **Auth**: None (Public endpoint).
- **Side effects**: Used by the registration flow to surface promotional codes before the user commits to a purchase.

## External consumers

- `concorda-web` (via `eventsApi.getDiscounts`)
