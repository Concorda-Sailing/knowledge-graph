---
node_id: concorda-web::src/lib/api.ts::eventsApi.getDetail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cca7f07934e47440a41fe9010c190fa8bf99eac176fe13b2472453f110a94df6
status: current
---

# eventsApi.getDetail

## Purpose

Client-side mirror for single-event detail. Calls `GET /api/events/{id}/detail` and returns one `ScheduleItem`-shaped row built by the backend's `_build_schedule_item_for_event` helper — the same helper that shapes every row of `mySchedule`. Added 2026-05-09 (commit `1b5d864 fix(schedule): detail page calls /api/events/{id}/detail, drops mySchedule coupling`) so the schedule detail page can refresh one event after a user action without re-fetching the entire `my-schedule` aggregate. If you need a fresh `ScheduleItem` for a known event id (post-bookmark, post-RSVP, post-crew-action), this is the call.

## Invariants

- Returns the same row shape as a single element of `eventsApi.mySchedule()` — the backend uses `_build_schedule_item_for_event` for both. Don't drift the TypeScript `ScheduleItem` type to fit one without the other.
- Authenticated only (`fetchApiAuthenticated`). The backend 403s when the viewer has no claim (not owner / bookmarker / registrant / crew / boat-owner of an assigned boat). 404 when the event id doesn't exist.
- Authz scope is **broader** than `mySchedule`'s: `mySchedule` is upcoming-only (it's a calendar feed), but `getDetail` lets you load past events you have a claim on. Don't conflate the two scopes.
- One of the four claims of `rule::schedule::canonical_listing` — adding a fifth schedule-shaped surface should route through `_build_schedule_item_for_event` and be documented in that rule, not built parallel to this.

## Gotchas

- Pre-`1b5d864`, the detail page derived its data by `find()`-ing the event id inside `mySchedule`'s response. That coupled detail rendering to the calendar-feed scope (so past events 404'd in the UI) and forced a full schedule refetch on every action. If you see code shaped like `mySchedule.find(e => e.id === id)` for detail purposes, replace it with `getDetail(id)`.
- Row shape is `ScheduleItem`, not `Event`. Don't reach for `eventsApi.get(id)` (public, returns bare `Event`) when the page expects sailing-event/viewer-role/crew-boats fields — that mismatch is what `1b5d864` fixed.
- All 6 known call sites live in `src/app/members/schedule/[id]/page.tsx::ScheduleEventDetail` (lines 162, 241, 413, 658, 686, 747). New consumers should be deliberate — anything beyond the schedule detail page wanting a `ScheduleItem` is a hint that the rule's "fifth surface" question may be relevant.

## Cross-cutting concerns

- **Auth:** authenticated endpoint; surfaces a 403 distinct from 404 so the UI can render "you don't have access" vs "doesn't exist" differently.
- **Cache coupling:** components calling this and `mySchedule()` should reconcile on event id — the rows are interchangeable by shape, so a successful `getDetail` can update an entry in a cached `mySchedule` list without reshaping.
- **No side effects** — pure GET, no audit, no websocket events.

## External consumers

None known. Web-only; the Expo iOS app currently uses `mySchedule` for its detail view. If/when the app gets a single-event refresh path, this is the endpoint to wire.

## Open questions

- Should the `ScheduleItem` TypeScript type be the formal contract enforced on both `mySchedule` and `getDetail`, or is the current "shape happens to match" arrangement enough? A schema-level guarantee would catch backend drift faster.
