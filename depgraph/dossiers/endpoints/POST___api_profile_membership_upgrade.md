---
node_id: POST::/api/profile/membership/upgrade
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9a1a78e4c09e8e6f6ec22a4bb9e8bea28a91ac00fc39f6e6d2481aab9e5f3366
status: llm_drafted
---

# POST /api/profile/membership/upgrade

## Purpose

Handles the transition of a user's membership tier. It validates the requested `product_slug` against the `TemporalProduct` table, ensures the user is not already on the target plan, and manages the lifecycle of `PersonProduct` associations. This is the primary endpoint for upgrading from free to paid tiers or switching between existing membership categories.

## Invariants

- **Requires `require_auth`** — The request must be authenticated via a valid bearer token.
- **Strict Product Validation** — The `product_slug` must exist in the `TemporalProduct` table with `category == "Membership"` and `is_active == True`.
- **Mandatory Transaction for Paid Plans** — If the `new_product.price > 0`, a `transaction_id` must be provided and must correspond to a `Transaction` with status `"Completed"` for that specific user and product.
- **Atomic Membership Swap** — The function deletes all existing `PersonProduct` entries for the user within the "Membership" category before creating the new association.
- **Returns `ProfileRead`** — The response body is the updated user profile object.

## Gotchas

- **Payment Verification Logic** — Per commit `74962cb`, this endpoint is part of the security hardening that binds paid registrations to specific events; the `transaction_id` check is critical to prevent unauthorized tier escalation.
- **Membership Category Cleanup** — The function explicitly deletes all `PersonProduct` entries where `category == "Membership"` for the user. If a new product is incorrectly tagged or if the category logic is altered, users may end up with zero active memberships.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to identify the `current_user`.
- **Websocket**: Emits `PERSON_UPDATED` event with the `person_id` upon successful commit.
- **Audit**: N/A.
- **Rate limit**: None explicitly defined in this router, but subject to global API rate limiting.
- **Side effects**: Triggers updates to any UI components listening to `PERSON_UPDATED` (e.g., user profile badges or subscription status indicators).

## External consumers

- `concorda-web` (via `profileApi.upgradeMembership`)
