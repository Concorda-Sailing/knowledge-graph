---
node_id: concorda-web::src/lib/api.ts::eventsApi.removeScheduleEvent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2547ad0105db797fd44f30d0823b613aa270eb2bc27c92c4c243bd1c2dd3d965
status: current
---

# eventsApi.removeScheduleEvent

## Purpose

Client-side mirror for the "remove from MY schedule" action — the partner of `addRegattas`/`addEvents` and the per-event sibling of `removeScheduleSeries`. Despite the name suggesting a simple unbookmark, the underlying `DELETE /api/events/my-schedule/events/{event_id}` is **role-polymorphic**: for a plain attendee it deletes the `PersonEvent` bookmark; for the personal-event owner it deletes the `Event` row; for a boat co-owner with a `SailingEvent` for this event it tears down the captain's plan (SE + EventCrew + crew bookmarks) and may delete an orphaned personal `Event`. The response shape (`removed`, `had_plan`, `crew_removed`) is the UI's only signal that a teardown happened, so callers branch their toasts on it. Future Claude: this is a "leave my schedule" verb, not "delete the public event" — but for captains it is also "cancel my race plan."

## Invariants

- The endpoint is **DELETE on a path with the source event ID**, not the user's PersonEvent ID. The server resolves which row to delete based on viewer role.
- Response is always `{ removed: boolean, had_plan: boolean, crew_removed: number }` — frontend treats `had_plan === true` or `crew_removed > 0` as "show 'plan was canceled, N crew notified' instead of 'removed from schedule.'"
- Calling this never deletes a non-personal `Event` or `Regatta`. Public events stay; only the caller's claim on them is severed.
- Per the `schedule__canonical_listing` rule, after success callers should refresh via `eventsApi.mySchedule()` (full list) or — newer pattern — `eventsApi.getDetail(id)` if showing a single event view post-action.

## Gotchas

- **It is not just a bookmark removal.** If the caller is a boat owner with a `SailingEvent` for this event, `_cleanup_sailing_event` runs: deletes EventCrew rows, sends `event_canceled` calendar emails to invited/accepted/confirmed crew, pulls those crew members' schedule bookmarks, deletes the SE, and (co-owner branch) may delete the underlying personal Event if no other SEs remain. UI that says "removed from your schedule" without surfacing `crew_removed > 0` will mislead a captain who just cancelled crew on N people.
- The endpoint has three fall-through branches (bookmark → personal-owner copy → co-owner SE) and returns 404 only if all three miss. A captain with no bookmark but with an SE still removes successfully via the third branch — frontend cannot assume "I had it on my schedule" implies a `PersonEvent` existed.
- `1b5d864 fix(schedule): detail page calls /api/events/{id}/detail, drops mySchedule coupling` — the schedule detail page (one of the 3 consumers) used to refetch the full schedule after this call. Don't reintroduce that coupling; use `getDetail` for single-event refresh.
- `synchronize_session="fetch"` + an explicit `db.flush()` after `_cleanup_sailing_event` in the co-owner branch — autoflush is off, so the orphan-Event check would see a stale SE without the flush. Keep it if editing.

## Cross-cutting concerns

- **Email side effects:** active crew (invited/accepted/confirmed) get an `event_canceled` calendar email when a captain's plan is torn down. Wrapped in `try/except` so a mailer failure doesn't block the delete — but it does mean a 200 response can hide partial email failure.
- **Auth:** `require_auth`. No org-admin override — this is strictly a self-service "my schedule" verb.
- **Cascades onto other users:** in the co-owner branch, *other* boat owners' bookmarks for this event are deleted too (they were tracking the boat's involvement, which just ended). They have no UI signal this happened until their next schedule fetch.
- **Series counterpart:** `removeScheduleSeries` walks every event in the series and calls the same teardown. Keep the per-event semantics aligned or the series version drifts.

## External consumers

None known. The 3 internal consumers are `regattas/page.tsx`, `schedule/[id]/page.tsx`, and `dashboard/schedule-tab.tsx`. No mobile/Expo, ICS, or webhook consumer hits this — the ICS feed is read-only.

## Open questions

- Should the captain-teardown path live behind a separate verb (e.g., `cancelMyPlan`) so the UI doesn't have to infer intent from `had_plan`/`crew_removed`? Today's three callers all branch on the response, which suggests the server is overloading one endpoint with two user intents.
- Co-owner removal silently deletes other owners' bookmarks. Should they get an in-app notification, or is the next schedule render enough?
