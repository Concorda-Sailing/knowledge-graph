---
node_id: concorda-test::lib/api-client.ts::ApiClient.createSailingEvent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3fdd7e39b690080e26083b1a9c0c443dbdd263efeb4ae61ac80e79f187285f20
status: current
---

# ApiClient.createSailingEvent

## Purpose
Test-harness wrapper for creating a SailingEvent (the captain's per-race plan) by hitting `POST /api/events/custom`. Used by 6 Playwright specs across `auth/`, `dashboard/`, `events/`, and `boats/` to seed a fresh (Event + SailingEvent) pair in one round trip, where the Event is `category=personal` owned by the calling user and the SailingEvent carries the chosen `event_subtype` (default `"race"`). The shape is *narrower* than `eventsApi.upsertSailingEvent` from the web client: it only accepts `name`, `date`, `event_type`, `boat_uuid` — i.e., enough to land a row that subsequent calls (`upsertSailingEvent`, `setEventCrewPool`, `sendEventCrewInvites`, etc.) can build on. It is the test-only counterpart to the captain's "Add custom race" UI flow; production web code does not have an equivalent helper because the UI inlines the same `/api/events/custom` call.

## Invariants
- The endpoint is `/api/events/custom` (not `/api/events`); `/api/events` lists, `/custom` is the atomic Event+SailingEvent creator.
- Wrapper aliases its `event_type` argument onto the API's `event_subtype` field — keep that mapping if either side renames.
- Default subtype is `"race"`; tests that need `training` / other subtypes must pass `event_type` explicitly (event-schedule.spec.ts:79,109,140 all pass `'training'`).
- Returns `{ id, slug? }` extracted from `resp.event` — callers use `id` for follow-up `/api/events/{id}/sailing-event*` paths; the `sailing_event` half of the response is intentionally discarded as `unknown`.
- Created events are personal-category and owned by the authenticated caller — visible via `/api/events/personal`, NOT via the public `/api/events` feed (see cross-context-crew.spec.ts:129-134).

## Gotchas
- **No name+date uniqueness on the server.** Each call seeds a fresh row, so retried Playwright tests will pile up duplicates unless the spec looks up first (cross-context-crew.spec.ts:126-147 does this; the others rely on `Date.now()` in the name + `removeScheduleEvent` cleanup in `finally`).
- Cleanup hygiene matters: most call sites pair this with `api.removeScheduleEvent(event.id).catch(() => {})` in a `finally` block. New callers that skip cleanup will leak rows on failed runs and the next run may collide on uniqueness assertions even without strict server-side guards.
- Despite the parameter name `event_type`, the field on the wire is `event_subtype` — the Event's `category` is hard-coded server-side to `personal` for this endpoint. Don't be fooled into thinking you can create a regatta-category event here.
- `boat_uuid` is optional in the wrapper signature but every current caller passes one — the server will create a SailingEvent without a boat if omitted, and the resulting row collides with the same anti-orphan guard documented for `upsertSailingEvent` (a subsequent first-time logistics PUT must include `boat_uuid` or the backend 400s).
- This wrapper does NOT run the auto-persist-boat shim that `schedule/[id]/page.tsx` runs in the UI; tests reaching the schedule detail page after seeding via this helper have already committed `boat_uuid` and skip the shim entirely — useful to know when adding a spec that exercises that fallback.

## Cross-cutting concerns
- Auth: caller must be logged in (`setToken` first); endpoint runs under `require_auth` and the new SailingEvent is bound to the caller's owned-boat row via `BoatCrew`.
- Side effect: like `upsertSailingEvent`, server may dispatch calendar emails on subsequent dock/logistics changes, but this initial create call does not (no `dock_time` is set yet).
- No websocket broadcast; specs that load the schedule page after seeding rely on a fresh navigation/fetch, not push.
- Disables Node TLS verification process-wide (`NODE_TLS_REJECT_UNAUTHORIZED=0` at module load) so the test host's self-signed cert is accepted — fine for the test VM, never import `lib/api-client.ts` from non-test code.

## External consumers
None. Test-harness only. Six Playwright specs.

## Open questions
- Should the wrapper accept the richer logistics fields (`dock_time`, `notes`, etc.) and forward them to `/api/events/custom` if the backend grows that — or stay minimal and force callers to chain `upsertSailingEvent`? Current callers always chain, so the split is fine, but it is two round trips per fully-set-up fixture.
- Is `category=personal` always the right seed for E2E? Tests that need to exercise regatta-bookmark flows currently can't use this helper and must go through `addRegattasToSchedule` instead — worth a sibling helper if that path grows test coverage.
