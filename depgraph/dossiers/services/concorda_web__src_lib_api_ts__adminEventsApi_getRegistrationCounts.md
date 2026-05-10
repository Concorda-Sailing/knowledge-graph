---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.getRegistrationCounts
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 17472b0b80d7d45abe0e36e0fbba4c5fd889471014a606234a8682fbafd93fe5
status: current
---

# adminEventsApi.getRegistrationCounts

## Purpose

Fetches a summary of registration counts across all events. It is used to provide high-level administrative visibility into total registration volume without requiring the client to iterate through individual event objects or fetch full registration lists.

## Invariants

- **Returns a `Record<string, number>`** where keys are event identifiers and values are the current registration counts.
- **Uses `fetchApiAuthenticated`** — requires a valid session token to access the `/api/events/registration-counts` endpoint.
- **Endpoint is global to events** — unlike `getRegistrations(id)`, this does not take an ID as an argument and returns a map of all event counts.

## Gotchas

- **Ambiguity in count types** — per commit `b4d60c6`, there is a distinction between "accepted invites" and "live slot counts." Ensure this endpoint is used for aggregate registration volume rather than specific invite-acceptance logic to avoid displaying incorrect state-driven counts.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Used by `SocialsPage` to display administrative overview data.

## External consumers

- `concorda-web::src/app/members/admin/events/socials/page.tsx` (via `SocialsPage`)
