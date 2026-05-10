---
node_id: concorda-web::src/lib/api.ts::eventsApi.addRegattas
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d9c36cfc024dedeaf9d01a42b48ebe6ad7aebdc14b89aab408091b1b09943514
status: llm_drafted
---

# eventsApi.addRegattas

## Purpose

Client-side mirror of `POST /api/events/my-schedule/add-regattas` — the bulk "register me for these races" endpoint. Powers the regatta browse → multi-select → add-to-schedule flow on `/members/regattas`. Accepts an array of regatta IDs and an optional captain payload (boat + dock/departure/duration/crew-pool defaults); without the captain payload it bookmarks the races as crew, with it the user is committing one of their boats to each race and a `SailingEvent` is pre-populated. The endpoint is idempotent on (user, event) and is the entry point feeding source #2 (bookmarks) and indirectly #5 (co-owned SailingEvents) of the `my-schedule` aggregator.

## Invariants

- The captain payload is all-or-nothing: passing any captain field without `boat_uuid` is a client-side bug — the backend keys captain mode on `boat_uuid is not None` and silently ignores the rest.
- Adding the same regatta a second time as crew is a no-op (PersonEvent uniqueness on person_uuid + event_uuid + relationship="schedule"); response `added` reflects net-new rows, not requested count.
- Captain-adding a regatta the user previously crew-bookmarked **upgrades** the existing PersonEvent.role to "captain" — there is no "downgrade captain → crew" path through this endpoint.
- A user can be captain on multiple boats for the same Event; SailingEvent is keyed by (event, boat), so re-calling with a different `boat_uuid` creates a second SailingEvent rather than clobbering the first.
- `dock_time` / `departure_time` are `"HH:MM"` 24h strings — the client must not send full ISO timestamps. The backend composes them onto `regatta.start`'s date.

## Gotchas

- **`addRegattas` does NOT create `EventRegistration` rows.** It writes `PersonEvent` (relationship="schedule") and optionally `SailingEvent`. The schedule shows up via the bookmark source in `my-schedule`, not the registration source. If you're hunting for "why isn't this race showing in my registrations list" — wrong endpoint.
- **No websocket event is emitted.** There is no `REGISTRATION_UPDATED` (or equivalent) broadcast from this handler today; consumers must refetch `mySchedule()` themselves. The regattas page tracks freshly-added IDs in local `addedIds` state to avoid the round-trip.
- **The default `departure_time = dock_time + 45m`** noted in the TS comment is a **client-side** default (api.ts:441) — the server does not synthesize it. If a future caller skips api.ts and posts directly, departure_time will be NULL.
- **Existing per-boat `SailingEvent` is preserved.** The captain branch explicitly bails (`if se: continue`) before overwriting dock/departure/duration on a SailingEvent the user may have customized race-by-race. Don't "fix" this without reading commit `bf15808` and the surrounding schedule reverts.
- Unknown `regatta_id`s are silently skipped (no 404), so `added < len(regatta_ids)` can mean either "already bookmarked" or "bad ID". The four call sites all conflate these into "Already on your schedule" — fine UX today but watch if a future caller needs to distinguish.

## Cross-cutting concerns

- **Auth:** `require_auth` only — any authenticated member can add any regatta to their own schedule. Captain mode additionally calls `_require_boat_owner(boat_uuid, current_user.id)` and validates `crew_pool_id` belongs to that boat.
- **Schedule rule:** This is a **write path** feeding source #2 of the `my-schedule` aggregator (see `rule::schedule::canonical_listing`). After a successful call, the canonical refresh path is `eventsApi.mySchedule()` or `eventsApi.getDetail(eventId)` — both go through `_build_schedule_item_for_event`.
- **Side effects:** May create a shared regatta `Event` row on first add by any user (the `Event` is shared across all users adding that regatta). May create per-(event,boat) `SailingEvent` rows in captain mode. May upgrade an existing PersonEvent role crew → captain.
- **No audit / no email / no websocket.** Pure DB writes plus a counts response.

## External consumers

None known. Browser-only flow on `/members/regattas`. The Expo iOS app does not yet wire a regatta browse surface.

## Open questions

- Should this fire a websocket event so other open tabs / the iOS app refresh `my-schedule` without a manual reload? The framing prompt referenced `REGISTRATION_UPDATED` — that channel doesn't exist today; if it's wanted, decide whether it fires from here, from `add-series`, from `add-events`, and from the deletion endpoints uniformly.
- The `added` counter mixes "already had it" with "regatta not found" — worth splitting if a future caller (admin tooling? CSV import?) needs to surface the distinction.
- No transactional boundary across regattas: a mid-loop failure commits the partial set on the next successful `db.commit()` call (currently only at the end, so a raised exception aborts cleanly — but the loop itself swallows missing regattas). Watch this if per-race validation grows.
