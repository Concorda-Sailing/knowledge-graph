---
node_id: concorda-web::src/lib/api.ts::eventsApi.mySchedule
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 828fa71fad79141f23e049262be4c038d148115eaa6159d9fd94395775a7056d
status: llm_drafted
---

# eventsApi.mySchedule

## Purpose

The thin frontend wrapper for `GET /api/events/my-schedule` — the **canonical** schedule feed (per `rule::schedule::canonical_listing`). Returns a deduped, date-sorted `ScheduleItem[]` aggregating five sources from the viewer's POV: owned personal events, schedule-bookmarks, Confirmed registrations, active EventCrew rows, and SailingEvents on co-owned boats. Upcoming-only: filtered server-side to `Event.date >= start-of-today UTC`. Companion to `eventsApi.getDetail(id)`, which returns one row in the same shape via the shared `_build_schedule_item_for_event` helper — that's the only sanctioned way to refresh a single event without re-pulling the whole feed. If a future surface needs schedule-shaped data, it must route through the helper and document its scope subset in the rule, not spawn a parallel implementation.

## Invariants

- Return shape is `ScheduleItem[]`; element shape MUST match what `_build_schedule_item_for_event` emits so `mySchedule()` and `getDetail()` payloads are interchangeable downstream.
- Dedup is server-side and keyed by `Event.id` — bookmarked + registered + crew on the same event collapses to one row.
- Date filter floor is **start-of-today UTC, not `now`** — events earlier today (e.g. an 11am dock time added at noon) must remain visible. Per-source filter, not a post-aggregation pass.
- Personal events (`owner_id == viewer`) appear even when the user has no other connection — this was the bug behind a recent revert/re-revert pair.
- Co-owned-boat events only surface for boats with **≥2 active owners**. Sole-owned boats already reach the viewer through personal/bookmarked buckets, and "Shared" has no meaning there.
- "External crew" tagging excludes EventCrew rows on boats the viewer owns — that's captaining, not crewing.
- No params: viewer is always `current_user`. Don't add a `user_id` query param; that breaks the canonical-feed framing.

## Gotchas

- `1b5d864` (2026-05-09): the detail page used to call `mySchedule()` and filter client-side to refresh one event. That coupled every single-event refresh to a 5-source aggregate query. Now `getDetail(id)` exists for that — do not regress.
- `bf15808`: don't shape-match to infer `boat_config_id`; use the stored value. Easy to reintroduce when "simplifying" the row builder.
- `b4d60c6`: accepted-invite count drives the Crew badge, not the position-name slot count. Position-name gating was wrong.
- The revert/re-revert pair (`7570175` → `57f2e00` → `b887b73`) was about user-owned personal events vanishing from the schedule. Date filtering is **per-source**; resist any refactor that consolidates it into one post-merge filter.
- `viewer_role` computation has subtle precedence: external EventCrew → "crew", crew-bookmark (without captain SE) → "crew", co-owned-only → "boat_co_owner", else null. A peer-boat EventCrew row should NOT outweigh the viewer's own captain commitment.

## Cross-cutting concerns

- **Auth**: `require_auth`; viewer identity drives every subquery.
- **Rate limits**: none documented on this route, but it's hit on dashboard mount + several pages — keep it cheap.
- **Side effects**: read-only.
- **Coupled mutating endpoints**: `add-regattas`, `add-series`, `add-events`, `DELETE /events/{id}`, `DELETE /series/{uuid}` all reshape what this feed returns. Frontend should refetch `mySchedule` (or call `getDetail` for one row) after these.
- **ICS feed** at `/api/schedule/feed/{token}.ics` mirrors the same scope serialized as iCalendar — scope drift here is an external-calendar bug. Verify alignment when adding a 6th source.

## External consumers

Direct callers (4):
- `src/app/members/regattas/page.tsx::RegattasPage` (two call sites)
- `src/app/members/socials/page.tsx::SocialsPage`
- `src/components/dashboard/schedule-tab.tsx::ScheduleTab`

The ICS feed at `/api/schedule/feed/{token}.ics` is a downstream sibling (same scope, different endpoint) consumed by external calendar apps via subscription — not a caller of this function but bound by the same scope contract.

## Open questions

- Should `mySchedule` accept a `?sources=` filter so callers can request a subset (e.g. crew-only) without spawning a new endpoint? Punted in the rule until a third use case appears.
- Calendar-feed dedup logic is independent of this function's dedup. Drift risk if scope diverges; no test pins them together yet.
