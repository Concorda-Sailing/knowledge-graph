---
node_id: concorda-web::src/lib/api.ts::profileApi.cancelEventRegistration
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9986502d26c4d7cd5874001166e8303c5f924aa926c3fa67dc7b504cc59ed3fa
status: llm_drafted
---

# profileApi.cancelEventRegistration

## Purpose

The `cancelEventRegistration` method handles the removal of a user's registration for a specific event. It is used when a user chooses to opt-out of an event they previously joined. This is distinct from `deleteCrewPool`, which manages the availability of crew slots, whereas this method specifically targets the user's personal registration record.

## Invariants

- **HTTP Method is `DELETE`** — The endpoint expects a deletion request to remove the registration.
- **Requires `id` parameter** — The registration ID must be passed as a string in the URL path.
- **Returns `{ message: string }`** — A successful call returns a confirmation message from the server.
- **Uses `fetchApiAuthenticated`** — The request is authenticated via the user's current session/token.

## Gotchas

- **Recent coupling changes** — Per commit `b4d60c6`, the system has moved away from strict "position-name" gating to ensure that count calculations (like accepted invites vs. live slots) remain accurate even when registration states change.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user can only cancel their own registrations.
- **Side effects**: Triggers updates to the `UpcomingEvents` component in the dashboard and the `MyEventsList` component in the user profile.

## External consumers

None known.
