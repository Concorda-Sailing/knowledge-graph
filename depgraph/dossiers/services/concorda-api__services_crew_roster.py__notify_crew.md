---
node_id: concorda-api::services/crew_roster.py::notify_crew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 77caceaff83ec3c2e43bddfbbbcf67c4a914eceb3304831e35063697e117ddb5
status: llm_drafted
---

# notify_crew

## Purpose

Transitions `EventCrew` records from `pool` status to `invited` status for a specific `SailingEvent`. It handles the logic of notifying members via multiple channels (email, SMS, WhatsApp) while ensuring the boat owner is not unnecessarily notified when they are the one initiating the invite.

## Invariants

- **Status Transition**: Moves `EventCrew.status` from `"pool"` to `"INVITED"`.
- **Owner Exception**: If `ec.person_uuid == inviter_id`, the status is set to `ACCEPTED` and no notification is sent.
- **Input Requirements**: Requires a valid `sailing_event_id` and an `inviter_id`.
- **Return Value**: Returns a list of all `EventCrew` records associated with the `sailing_event_id` after the status updates are flushed.

## Gotchas

- **Owner Self-Invite Logic**: Per commit `869af72`, the function must explicitly check if the inviter is the boat owner to prevent sending a notification to the person who just triggered the action.
- **Timezone Formatting**: The `_format_event_date` helper relies on `_to_org_local` to ensure the event date is rendered in the organization's local timezone rather than UTC, preventing the "wrong time" bug addressed in commit `6c314f5`.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers external notifications (Email, SMS, WhatsApp) via `_send_crew_notification`.

## External consumers

None known.
