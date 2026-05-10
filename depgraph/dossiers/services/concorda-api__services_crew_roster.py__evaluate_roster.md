---
node_id: concorda-api::services/crew_roster.py::evaluate_roster
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: efb268f87228466bbf1530ed6043ecd5bbd5e313b7f58c63f8992b4cca4fa17e
status: current
---

# evaluate_roster

## Purpose

Re-evaluates the crew roster for a specific sailing event to fill vacancies. When a primary crew member declines, this function identifies the highest-priority alternates (those in `pool` or `invited` status) and promotes them to the `main` role. It is distinct from simple roster viewing as it actively mutates the state of `EventCrew` records and triggers notifications.

## Invariants

- **Input is a `sailing_event_id`** which must correspond to a valid `SailingEvent`.
- **Returns a list of `EventCrew` objects** that were newly promoted or invited during the call.
- **Promotes by role and status**: If an alternate is in `EventCrewStatus.POOL`, their status is updated to `EventCrewStatus.INVITED` upon promotion.
- **Maintains priority order**: Alternates are sorted by `ec.priority` before promotion to ensure the most relevant members are moved up first.

## Gotchas

- **Notification logic is sensitive to ownership**: Per commit `869af72`, the system must ensure it does not notify a boat owner when they are inviting someone from their own pool, to avoid redundant or annoying notifications.
- **Role/Status dependency**: Promotion logic relies on the `EventCrewStatus` enum (introduced in commit `dd72f2f`). If a status is not handled in the `if/elif` block, the user may be promoted to `main` without receiving the necessary `INVITED` status or notification.

## Cross-cutting concerns

- **Auth**: None (relies on the caller to ensure the user has permission to trigger roster changes).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers `_send_crew_notification` which may result in email/push notifications to the promoted user.

## External consumers

None known.
