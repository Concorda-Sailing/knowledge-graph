---
node_id: POST::/api/events/{0}/sailing-event/crew-invite
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 21311e1079ea79c505b0ecf785157cb791c08a59761cad1db5f0adb25c0f4f89
status: llm_drafted
---

# POST /api/events/{event_id}/sailing-event/crew-invite

## Purpose

Sends invitations to members of the crew pool for a specific sailing event. It handles both targeted invites (specific `person_uuids`) and bulk transitions (moving all current "pool" members to an "invited" status). This method is distinct from the crew pool management endpoint, as it specifically triggers the transition from passive pool membership to active invitation and triggers notifications.

## Invariants

- **Requires Owner status** — The `current_user` must be the owner of the sailing event, verified via `_get_user_sailing_event_or_404`.
- **Returns a list of `EventCrewRead` objects** — The response contains the updated state of the affected crew rows.
- **Status transition logic** — If a person is already "accepted" or "confirmed", their status is not downgraded; they remain in their current state.
- **Self-invite behavior** — If the `current_user` is included in the `person_uuids`, they are automatically set to `ACCEPTED` rather than `INVITED` to prevent unnecessary notification/decision loops.

## Gotchas

- **Co-owner auto-acceptance bug** — Per the logic in `_set_invite_status`, co-owners are now explicitly given an `INVITED` status rather than being auto-accepted. This was implemented to prevent co-owners from being silently added to two boats' rosters without a chance to decline (see source comment: "Co-owners must get a real invite so they can decline if double-booked").
- **Notification suppression** — The system specifically filters `to_notify` to only include those with `status="invited"`. This ensures owners/self-inviters do not receive redundant notifications for actions they initiated.
- **Timezone-aware email body** — The email notification logic relies on `_to_org_local` and `org_tz` to ensure the event date in the invite is rendered in the organization's local time, not UTC (see commit `6c314f5`).

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (Owner/Admin level via `_get_user_sailing_event_or_404`).
- **Websocket**: Emits `EVENT_CREW_UPDATED` via `broadcast_event` to update live views.
- **Audit**: N/A.
- **Rate limit**: None specified.
- **Side effects**: Triggers email notifications via `notify_person` and updates the crew roster visibility in the schedule detail page.

## External consumers

- `concorda-web` (via `eventsApi.sendCrewInvites`)
- `concorda-test` (via `ApiClient.sendEventCrewInvites`)
