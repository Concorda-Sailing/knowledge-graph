---
node_id: concorda-web::src/lib/api.ts::calendarApi.status
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cfba604f8e4ec9c6425e99d2d2c1b4673c42407382394729c75ae9e21b461ec0
status: llm_drafted
---

# calendarApi.status

## Purpose

Provides the interface for managing the user's external calendar subscription status. It allows the client to check if a subscription is active, rotate the token (re-issue a new URL), or disable the subscription entirely. This is distinct from `policiesApi` or `membership`-related calls, as it specifically manages the lifecycle of the `webcal` and `subscription_url` endpoints.

## Invariants

- **Uses `fetchApiAuthenticated`** — All calls to `status`, `rotate`, and `disable` require a valid bearer token.
- **`status` returns `CalendarTokenStatus`** — Provides the current `subscription_url` and `webcal_url`.
- **`rotate` is a `POST` request** — Used to refresh the subscription URLs.
- **`disable` is a `DELETE` request** — Effectively terminates the active calendar subscription.

## Gotchas

- **`rotate` vs `disable` order** — While not explicitly a bug in the code, the `rotate` method is the primary way to refresh the `webcal_url` if the existing one becomes stale or invalid.
- **Dependency on `fetchApiAuthenticated`** — If the authentication layer fails or the token is expired, `status` will fail to return the current subscription state, which could lead to the UI showing an incorrect "disconnected" state.

## Cross-cutting concerns

- **Auth**: Requires `fetchApiAuthenticated` (bearer token).
- **Side effects**: Changes to the status (via `rotate` or `disable`) directly affect the availability of the calendar feed used by external calendar applications.

## External consumers

- `CalendarSubscriptionSection` in `concorda-web/src/components/profile/sections/calendar-subscription-section.tsx`.
