---
node_id: concorda-web::src/lib/api.ts::eventsApi.getConfirmation
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6ae121738caee7261c271ca4bcd26dccc932e45af52b9154ef6f88fb4c868a83
status: current
---

# eventsApi.getConfirmation

## Purpose

Fetches the registration confirmation details for a specific user at a specific event. It retrieves a list of registration objects (including `ticket_name`, `status`, and `transaction_id`) by matching a unique `slug` and a `regId`. This is used by the public event view to display success states or status updates to a user who has just registered or checked in.

## Invariants

- **Method is GET** — Uses a query parameter `reg` to identify the registration.
- **Input is URL-encoded** — The `regId` must be passed through `encodeURIComponent` to ensure the request is valid.
- **Returns an array of objects** — Even if there is only one registration, the return type is `Array<{...}>`.
- **Requires a valid event slug** — The slug is a required part of the path.

## Gotchas

- **Coupling with `mySchedule`** — Per commit `1b5d864`, there was a previous issue where the detail page was too tightly coupled to `mySchedule`; ensure this endpoint remains a lightweight fetch for specific registration status rather than a full schedule load.
- **Registration vs. Identity** — This endpoint relies on a `regId` (registration ID) rather than a user ID, making it a public-facing lookup for a specific registration event.

## Cross-cutting concerns

- **Auth**: None. This is a public-facing endpoint used by `PublicEventPage` to show registration status without requiring a logged-in session.
- **Side effects**: Used by `PublicEventPage` to render the post-registration/check-in state for a user.

## External consumers

- `concorda-web::src/app/events/[slug]/page.tsx::PublicEventPage` (via `hook_call`)
