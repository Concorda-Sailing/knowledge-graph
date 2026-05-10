---
node_id: GET::/api/temporal-products/available
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0556d834acb82fdd62841946c926c60debcb3f3bcc091ab36e2ea8b6dc2c00aa
status: current
---

# GET /api/temporal-products/available

## Purpose

Provides a public-facing list of available temporal products (e.g., Memberships or Events) for a given year and category. This is a read-only endpoint used by the registration flows to show users what they can sign up for. It is distinct from the admin `GET /` endpoint, which contains the logic for auto-copying products from previous years.

## Invariants

- **HTTP Method:** `GET`
- **Auth:** None required (Public endpoint).
- **Return Shape:** `list[TemporalProductPublic]`.
- **Default Year:** If `year` is not provided, it defaults to the current calendar year.
- **Filtering:** Supports optional `year` (int) and `category` (string: "Membership" or "Event").
- **Ordering:** Results are returned ordered by `sort_order`.

## Gotchas

- **No Mutation Allowed:** This endpoint is strictly read-only. Per the docstring, the "lazy auto-copy from a prior year" logic is explicitly gated to the admin endpoint to prevent unauthenticated callers from triggering database writes (as noted in the source docstring).
- **Security Fix:** Recent commit `ec53704` addressed a vulnerability where unauthenticated DB writes could be triggered; ensure any logic added here remains side-effect free to avoid re-opening the "unauth DB write" surface.

## Cross-cutting concerns

- **Auth**: None (Public).
- **Rate limit**: None (though `ec53704` indicates rate limiting is enforced on auth endpoints, this specific endpoint is currently unlisted in the rate-limit hardening).
- **Side effects**: None.

## External consumers

- `concorda-test::lib/api-client.ts::ApiClient.getAvailableProducts` (used for testing registration flows).

## Open questions

- Should the `category` filter be an Enum rather than a raw string to prevent invalid query parameters from being passed by the client?
