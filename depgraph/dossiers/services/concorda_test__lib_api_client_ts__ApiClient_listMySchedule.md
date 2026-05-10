---
node_id: concorda-test::lib/api-client.ts::ApiClient.listMySchedule
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f1f89e1d52f0defae31c9e2427643c684527f70938c7d501106581caa5af195e
status: llm_drafted
---

# ApiClient.listMySchedule

## Purpose

Retrieves the current user's personalized schedule, which is a composite view of multiple event types. It aggregates personal events, bookmarked items, registered events, and crewed events into a single list. Use this method when a test needs to verify that a user's dashboard or "My Schedule" view correctly reflects their current commitments.

## Invariants

- **HTTP Method is `GET`** — calls the `/api/events/my-schedule` endpoint.
- **Returns `ScheduleItem[]`** — the response is a typed array of objects representing upcoming commitments.
- **Requires Authentication** — relies on the `ApiClient` instance having a valid bearer token established via a login method.

## Gotchas

- **Integration with UI state** — per commit `c8b6d75`, this method is critical for verifying that the "Boats" tab and "My Schedule" view correctly reflect crew/event visibility for the user.
- **Dependency on global setup** — as part of the `ApiClient` suite, it assumes the user identity is correctly established via the `globalSetup` logic (see commit `c70d472` regarding policy acceptance in setup).

## Cross-cutting concerns

- **Auth**: Requires a valid session token; failure to login first results in an empty list or 401.
- **Side effects**: The contents of this list are directly affected by the results of `addRegattasToSchedule` (which can create `SailingEvent` entries) and `respondToInvite` (which updates status).

## External consumers

None known.
