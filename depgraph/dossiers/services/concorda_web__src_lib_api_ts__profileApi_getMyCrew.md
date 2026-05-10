---
node_id: concorda-web::src/lib/api.ts::profileApi.getMyCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c1f122143f667efaac622c1bfeb81660090908eab73e7aba23cdca34e740cc24
status: current
---

# profileApi.getMyCrew

## Purpose

Client-side mirror for `GET /api/profile/crew` — returns the unified `MyCrewData` shape (`owned_boats[]`, `invitations[]`, `event_invitations[]`, `crewed_boats[]`) in one round trip. It is the richer cousin of `getBoats` (which is owned-only and returns bare `Boat[]`); `getMyCrew` is the right call whenever the UI needs to render either side of the owner/crew relationship, the inbox of pending boat-crew invitations, or the inbox of pending event-crew invitations. Four call sites consume it: the main `MyCrewTab` (the dashboard's My Crew page), `BoatsList` in the boats tab (renders the boat cards with their crew), `ScheduleTab` (uses `event_invitations` for the "incoming invites" surface), and `useDashboardBadges` (drives the unread-count badges from `invitations.length + event_invitations.length`). Future Claudes deciding between `getMyCrew` / `getBoats` / `listCrewPools`: pick `getMyCrew` for the person-centric "everything that involves me and a boat" view, `getBoats` only when you literally need the owned-boat list with no crew detail, and `listCrewPools` only for boat-scoped CrewPool rows (a different domain object — see Gotchas).

## Invariants

- Endpoint is `/api/profile/crew`, GET, authenticated. There is no boat-id parameter — scope is always "me, the current user."
- Response shape is exactly `{ owned_boats, invitations, event_invitations, crewed_boats }`. Frontend `MyCrewData` and the backend dict literal in `routers/profile.py:get_my_crew` are coupled — adding/renaming a key requires touching both.
- `owned_boats[].crew` includes the owner themselves (the backend pulls all `BoatCrew` rows for the boat, not just non-owners). UIs that show "my crew" lists must filter out `role=="owner"` if they want crew-only.
- `crewed_boats[]` only includes `role="crew"` + `status="active"` memberships — invited/declined/prospective non-owner memberships do NOT appear here; pending ones land in `invitations[]` instead.
- `invitations[]` contains only `BoatCrew` rows where `status=="invited"` for the current user. `event_invitations[]` is the EventCrew analogue with the same status filter.
- Each `BoatCrewMember` in `owned_boats[].crew` carries `priority: number` — the click-order priority from the invite dispatcher. Don't drop it; the consolidated crew card and pool-ranking UIs read it.

## Gotchas

- The crew-priority system landed via `b986a9e feat(my-crew): include priority in get_my_crew response`. Older clients that didn't read `priority` are gone — assume it's always present. If you change the shape, the consolidated crew card on `MyCrewTab` and the priority-ordered invite picker break silently (no type error if you only mutate the backend dict).
- `crewed_boats[]` was added in the My Crew UX overhaul (Apr 9 session). Before that, non-owner sailors saw nothing in this response. Code that predates the overhaul may still assume "owned_boats means all my boats" — verify when touching legacy call sites.
- `770d190 refactor(crew-pools): scope pools to boat instead of person` is the closest cousin commit and the source of a recurring confusion: **CrewPools are boat-scoped objects fetched via `listCrewPools(boatId)`**, NOT included in `MyCrewData`. "My Crew" the dashboard tab is a person-owned logical grouping; CrewPools are a separate per-boat construct. Don't try to merge them.
- Backend issues N+1 queries (per-boat crew fetch, per-crew person lookup, per-invite boat/inviter lookup, per-event-invite multi-table join). Fine at current scale but will bite if a single user owns dozens of boats with many crew each — don't add more per-row queries without profiling.
- `event_invitations[].open_positions` is computed by subtracting taken slots from `positions_needed`; the recent `b4d60c6 fix(schedule): count accepted invites vs live slot count` and `bf15808 fix(schedule): use stored boat_config_id instead of shape-matching` show this area is fragile. If you change position semantics, retest the schedule tab's invite display.
- `1b5d864 fix(schedule): detail page calls /api/events/{id}/detail, drops mySchedule coupling` — schedule detail no longer derives from `getMyCrew`. Don't reintroduce the coupling; keep this endpoint focused on the dashboard inboxes/cards.

## Cross-cutting concerns

- **Auth**: `require_auth` — any authenticated member. No org-scoping check; the response is naturally scoped by `current_user.id`.
- **Rate limits**: none specific. Called on every dashboard mount and on `useDashboardBadges` polling — be mindful before adding heavier work to the handler.
- **Crew visibility / privacy**: this endpoint returns full crew identity (`person_first_name`, `person_last_name`, `person_email`, `person_picture_url`) for owned boats. That's intentional — the viewer is the owner. Do NOT extend this endpoint to expose other people's boats' crew without applying the [crew peer visibility](feedback_crew_visibility_privacy.md) rule (hide peer identities unless resume is published).
- **Side effects**: read-only. No audit log, no websocket events.
- **Datetime**: `created`/`modified` fields are returned as raw `UtcDateTime` values; consumers must format with `lib/datetime.ts` helpers and the org timezone — never `toLocaleString()` without `timeZone`.

## External consumers

None known. Internal to the web client (and presumably to the Expo app's My Crew screen if/when it ports — verify before assuming).

## Open questions

- Should `owned_boats[].crew` exclude the owner row, or is leaving it in (and filtering client-side) the contract? Current consumers all filter; consolidating would simplify but breaks anything that wants the owner included.
- N+1 is tolerable now but unbounded in boats × crew. Worth a single eager-loaded query if any user crosses ~20 boats.
- `event_invitations` lives here for inbox convenience but is conceptually an event-domain object. If a future redesign splits the dashboard inbox into its own endpoint, this response could shed two of its four keys.
