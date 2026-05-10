---
node_id: concorda-web::src/lib/api.ts::calendarApi.disable
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1a4e9d0af714406894712cdd95a4e8a080c4bda6f2e18f22a343c35941e8e67e
status: current
---

# calendarApi.disable

## Purpose

The `disable` method on `calendarApi` is used to revoke a user's calendar subscription/token. It performs a `DELETE` request to the `/api/calendar/token` endpoint. This is a destructive action used to disconnect the calendar integration from the user's account.

## Invariants

- **HTTP Method is `DELETE`** — The endpoint specifically requires a DELETE verb to clear the existing token.
- **Uses `fetchApiAuthenticated`** — This call requires a valid bearer token to succeed; it is not a public endpoint.
- **Returns `void`** — The API response body is ignored by the client-side type definition, as the primary side effect is the removal of the token.

## Gotchas

- **Requires authenticated context** — Because it uses `fetchApiAuthenticated`, any component attempting to call this must ensure the user is logged in, or the request will fail with a 401/403.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is tied to the current user's session.
- **Side effects**: Disabling the calendar token will impact the `CalendarSubscriptionSection` (specifically `calendar-subscription-section.tsx:53`), which monitors the presence of this token to render the subscription UI.

## External consumers

- None known.
