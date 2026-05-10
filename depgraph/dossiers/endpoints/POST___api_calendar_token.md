---
node_id: POST::/api/calendar/token
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8e8daae6456885b126e4175c383fa0b68ff4ad1f8d905b85bc7795af93f984db
status: llm_drafted
---

# POST /api/calendar/token

## Purpose

Generates a new, unique calendar token for the authenticated user, effectively rotating the existing one. This is used to refresh the `subscription_url` and `webcal_url` for external calendar clients. Use this endpoint when a user needs to reset their calendar access or when a security rotation is required.

## Invariants

- **Method is POST** to `/api/calendar/token`.
- **Requires authentication** via the `require_auth` dependency.
- **Returns a JSON object** containing `subscription_url` and `webcal_url`.
- **Mutates `Person.calendar_token`** in the database via `_generate_token()`.
- **URLs are constructed using `web_base_url`** from the global email configuration.

## Gotchas

- **Token rotation breaks existing clients.** Per `delete_token` logic, once a token is rotated or deleted, existing calendar subscriptions will 404 on the next refresh.
- **Timezone rendering dependency.** Per commit `6c314f5`, ensure that any logic consuming these URLs (like the `.ics` generation) respects the organization's timezone rather than defaulting to UTC, otherwise, the calendar display will be offset.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth`.
- **Audit**: N/A.
- **Side effects**: Rotating the token invalidates all previous `webcal_url` links for the user's external calendar applications.

## External consumers

- `concorda-web` (via `calendarApi.rotate`).
- External calendar clients (Google Calendar, Apple Calendar) via the generated URLs.
