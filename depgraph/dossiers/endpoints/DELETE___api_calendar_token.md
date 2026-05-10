---
node_id: DELETE::/api/calendar/token
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fff85fd6c6495b3df5f1f882cfbdca7faeea0a9a9bafd876e68284f17d8d5977
status: current
---

# DELETE /api/calendar/token

## Purpose

Disables the user's external calendar subscription by nullifying the `calendar_token` in the `Person` record. This is the backend implementation for the "Disable Subscription" action in the UI. It is distinct from simply hiding the feed; it actively breaks the link so that existing calendar clients (like Apple Calendar or Google Calendar) will receive a 404 or error on their next refresh, effectively stopping the sync.

## Invariants

- **HTTP Method is `DELETE`** — used to signal the destruction of the subscription link.
- **Returns `204 No Content`** — the response body is empty upon success.
- **Requires `require_auth`** — the endpoint is protected; only the authenticated user can delete their own token.
- **Mutates `person.calendar_token` to `None`** — the primary side effect is the removal of the string-based token from the database.

## Gotchas

- **Existing clients will 404** — per the docstring, once this is called, any external client relying on the `webcal_url` or `subscription_url` will fail to refresh.
- **URL construction depends on `web_base_url`** — the `_build_subscription_url` and `_build_webcal_url` functions rely on the `config["web_base_url"]` retrieved from the DB; if the base URL is misconfigured, the URLs provided by the GET counterpart (not this DELETE) will be broken.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth`.
- **Side effects**: Disables the external calendar sync for the user's schedule.

## External consumers

- `concorda-web` via `calendarApi.disable` (api.ts:241).
