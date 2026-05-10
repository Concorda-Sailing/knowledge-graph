---
node_id: concorda-test::lib/api-client.ts::ApiClient.listRegattas
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e8eebef3a03cf06744def06d649e8b9efe4f82357762e1c249e504b647572e67
status: current
---

# ApiClient.listRegattas

## Purpose

Fetches the list of available regattas from the API. This is a read-only helper used to populate discovery views where users browse upcoming events. It is distinct from `listMySchedule`, which returns a filtered view of events specifically relevant to the authenticated user's current status (bookmarked, registered, or crewed).

## Invariants

- **Returns an array of objects** containing `id`, `name`, `start`, `end`, and an optional `location`.
- **`start` and `end` are nullable strings.** The API may return `null` for events with TBD dates; callers must handle these as non-date types.
- **Uses a `GET` request** to the `/api/regattas` endpoint.
- **Requires authentication.** The `ApiClient` instance must have a valid bearer token established via a login method before calling this.

## Gotchas

- **Policy-based access:** Per commit `c70d472`, the test suite must ensure that pending policies are handled correctly; while this method is a simple GET, the underlying API may gate access or behavior based on the user's TOS acceptance status.
- **Data availability:** Tests relying on specific regatta names or dates must ensure the test database is seeded with regatta data, as this method only fetches what is currently in the registry.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token (typically established via `ApiClient.login`).
- **Side effects**: Used by the "My Schedule" and "Regatta Discovery" views in the E2E test suite to verify event visibility.

## External consumers

None known.
