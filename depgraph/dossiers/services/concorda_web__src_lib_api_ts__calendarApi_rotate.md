---
node_id: concorda-web::src/lib/api.ts::calendarApi.rotate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a609592c2c13a3c5e6ff3e268b05130f02333e7ee77b70decd23d5a12f1970d2
status: llm_drafted
---

# calendarApi.rotate

## Purpose

Generates and rotates the authentication tokens required for external calendar subscriptions. It provides the `subscription_url` and `webcal_url` necessary for users to sync their local calendars with the Concorda platform. Use `rotate` to generate a new set of credentials or `disable` to revoke existing access.

## Invariants

- **Method is POST** — `rotate()` must use the `POST` method to trigger a new token generation.
- **Returns `CalendarTokenIssued`** — the response must contain both `subscription_url` and `webcal_url`.
- **Requires Authentication** — uses `fetchApiAuthenticated` to ensure the user has a valid session before attempting to rotate or disable the token.

## Gotchas

- **`disable()` is destructive** — calling this method will invalidate the current subscription URLs, which may cause external calendar clients to lose sync or show errors until a new `rotate()` is called.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires a valid user session).
- **Side effects**: The `CalendarSubscriptionSection` component in the profile section relies on this to manage the user's subscription state.

## External consumers

None known.
