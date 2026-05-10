---
node_id: GET::/api/calendar/token
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3c3a43472517597641fd00b31f2371b4ff37f2fc3ecb9f29a4efb973fbebe327
status: current
---

# GET /api/calendar/token

## Purpose

Provides the status and management of a user's calendar subscription token. It allows users to check if a subscription URL is active and provides the necessary URLs (`webcal://` and `https://`) for external calendar clients (like Apple Calendar or Google Calendar) to ingest their schedule. Use this endpoint to determine whether to show the "Sync to Calendar" UI or to trigger a token rotation/regeneration.

## Invariants

- **Requires `require_auth`** — The endpoint is protected; it returns a 401/403 if a valid session is not present.
- **Returns a boolean status** — The response shape is either `{"has_token": false}` or `{"has_token": true, "subscription_url": string, "webcal_url": string}`.
- **`POST` rotates existing tokens** — Calling the POST method generates a new token and invalidates the previous one, which will break existing external calendar subscriptions.
- **`DELETE` clears the token** — Setting the token to `None` in the database results in a 204 response and effectively disables the feed.

## Gotchas

- **Timezone-aware rendering** — Per commit `6c314f5`, the `.ics` feed and email bodies must be rendered in the organization's local timezone, not UTC, to prevent schedule drift in the user's external calendar client.
- **Token rotation is destructive** — Because `create_or_rotate_token` generates a new `person.calendar_token`, any external calendar client currently using the old URL will immediately lose access to updates.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` (user session).
- **Side effects**: Rotating the token via `POST` affects the availability of the public `.ics` feed for the user.

## External consumers

External calendar clients (Apple Calendar, Google Calendar, etc.) via the `webcal_url` and `subscription_url`.
