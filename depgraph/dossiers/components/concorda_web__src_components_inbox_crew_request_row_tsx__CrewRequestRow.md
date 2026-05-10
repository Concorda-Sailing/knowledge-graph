---
node_id: concorda-web::src/components/inbox/crew-request-row.tsx::CrewRequestRow
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 20b8be1c6d34d60769bf16759bae9b826efc57f02711c6001fd502d7ac817046
status: current
---

# CrewRequestRow

## Purpose

Displays a single pending crew request within the user's inbox. It provides the requester's name, the event name, the boat identifier, and the event date. It allows the user to either accept or decline the request via the `eventsApi`, triggering a state refresh via the `onChanged` callback.

## Invariants

- **`req.event_date` must be a UTC ISO string.** It is passed to `formatInOrgTz` to ensure the date is rendered in the organization's local time, not the browser's.
- **`onChanged` is a required callback.** It must be called after a successful `respond` call to refresh the inbox list (e.g., to remove the row once the request is processed).
- **`respond` is asynchronous.** The `busy` state is used to disable both "Accept" and "Decline" buttons during the flight of the API call to prevent double-submissions.
- **`req.event_id` and `req.requester_id` are required.** These are the primary keys used by `eventsApi.respondToCrewRequest` to identify the transaction.

## Gotchas

- **Timezone rendering must be explicit.** Per commit `f444b4c`, all backend datetimes must be rendered using `formatInOrgTz` with the `timezone` from `useConstants`. Using a standard `toLocaleDateString` or a naked `Date` object will result in the wrong local time for the organization.

## Cross-cutting concerns

- **Auth**: Relies on `eventsApi.respondToCrewRequest`, which requires an authenticated session.
- **Side effects**: Successful interaction triggers `onChanged`, which typically refreshes the inbox list view.

## External consumers

None known.
