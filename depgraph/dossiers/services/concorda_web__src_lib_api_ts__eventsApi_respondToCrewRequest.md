---
node_id: concorda-web::src/lib/api.ts::eventsApi.respondToCrewRequest
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9f493f1b7cf9687241d13eb0c45a95d388225e9e2aa904dd8677137846e66b23
status: current
---

# eventsApi.respondToCrewRequest

## Purpose

Handles the finalization of a crew request by allowing a user to either accept or decline an incoming request. This method is the terminal step in the `requestToCrew` flow, transitioning a pending request into a formal membership status. It is distinct from `requestToCrew`, which initiates the request, and `updateMyPosition`, which manages general role placement.

## Invariants

- **HTTP Method is `PUT`** — The endpoint expects a state-changing update to an existing resource.
- **Requires `eventId` and `personUuid`** — Both the event context and the specific person's identity are required to target the correct request.
- **Action is strictly typed** — The `action` parameter must be exactly `"accept"` or `"decline"`.
- **Returns `EventCrewMember`** — The response provides the updated membership state, confirming the successful transition.
- **Uses `fetchApiAuthenticated`** — The request must be made with a valid bearer token.

## Gotchas

- **Ownership requirement** — Per commit `47688ac`, accepting a co-owner invite requires the user to have Boat Owner membership. If the user lacks this, the action may fail or be unauthorized.
- **Status-driven UI** — Per commit `2d6b8a7`, the UI (specifically the schedule card) relies on the successful execution of this call to update the "accepting-crew" status and counts.
- **Implicit dependency on `requestToCrew`** — This method is useless without a prior successful call to `requestToCrew` (which passes the `boat_uuid` and `notes`), as it acts on the resulting resource.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid user session).
- **Side effects**: Updates the "accepting-crew" status on the regatta detail page and updates the count on the schedule card.

## External consumers

- `ScheduleEventDetail` in `src/app/members/schedule/[id]/page.tsx`.
- `CrewRequestRow` in `src/components/inbox/crew-request-row.tsx`.
