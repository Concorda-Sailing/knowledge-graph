---
node_id: GET::/api/events/slug/{0}/tickets
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c15092b3b3965fbb06c9ffbfa835b403f1be591c3bdc4e9d2f5d7795f8b3893
status: current
---

# GET /api/events/slug/{slug}/tickets

## Purpose

Fetches the list of available ticketed products for a public event via its slug. This is the primary endpoint for the public-facing event detail page to display what can be purchased. It differs from `/api/events/{id}/detail` by focusing specifically on the `Product` availability and the `EventTicketPublic` schema rather than the full event metadata.

## Invariants

- **HTTP Method:** `GET`.
- **Path:** `/api/events/slug/{slug}/tickets`.
- **Return Shape:** A list of `EventTicketPublic` objects containing `id`, `name`, `slug`, `description`, `price`, and a boolean `available`.
- **Availability Logic:** A product is marked `available: true` only if its `quantity` is not null AND the current count of `EventRegistration` records with status `"Confirmed"` is strictly less than the product's `quantity`.
- **Registration Deadline:** If the event has a `registration_deadline` and the current UTC time is past that deadline, the endpoint returns an empty list `[]` instead of the products.

## Gotchas

- **Registration Deadline vs. Display:** If the `registration_deadline` is reached, the entire list is wiped (returns `[]`). This is a hard cutoff.
- **Strict "Confirmed" Status:** The availability calculation only counts registrations where `status == "Confirmed"`. If a user is in a "Pending" or "Cancelled" state, they do not count against the `quantity` limit.
- **Slug Collisions:** Per commit `4fd165d`, slugs for personal events are dropped to avoid global `UNIQUE` constraint collisions in the database. Ensure the `slug` passed is the public event slug, not a user-specific identifier.

## Cross-cutting concerns

- **Auth**: None (Publicly accessible via event slug).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The availability of tickets is a dependency for the frontend's "Buy" button state.

## External consumers

- `concorda-web`: Used by `eventsApi.getTickets` to populate the ticket selection UI on the event detail page.
