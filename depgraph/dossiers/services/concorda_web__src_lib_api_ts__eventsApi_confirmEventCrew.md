---
node_id: concorda-web::src/lib/api.ts::eventsApi.confirmEventCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 12f1ab332e573ca6a38c0b7e76c2f72a5a3a6d1772b090eb154460fe43e2e0bf
status: llm_drafted
---

# eventsApi.confirmEventCrew

## Purpose

Finalizes the crew assignment process for a specific sailing event. It transitions the event state to a state where crew members are officially confirmed, typically used when an organizer or automated process validates the current crew list. This is distinct from `markCrewResponse`, which handles individual accept/decline actions, and `requestToCrew`, which initiates the request.

## Invariants

- **HTTP Method is `POST`** — unlike the `PUT` or `DELETE` methods used by sibling crew functions.
- **Requires `eventId`** — the endpoint is scoped to a specific event path.
- **Returns `SailingEvent`** — the response provides the updated state of the full event object.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to execute.

## Gotchas

- **State-driven UI visibility** — per commit `2d6e4a1`, this call is part of the logic that drives the "accepting-crew" status on regatta detail pages and the config-aware count on schedule cards.
- **Coupling to detail views** — commit `1b5d864` indicates that event detail calls must be carefully managed to ensure that state changes triggered by crew confirmation are reflected in the detail view without stale data.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Triggers updates to the "accepting-crew" status on the regatta detail page and updates the count displayed on the schedule card.

## External consumers

- `concorda-web::src/components/dashboard/event-plan-panel.tsx::EventPlanPanel`
