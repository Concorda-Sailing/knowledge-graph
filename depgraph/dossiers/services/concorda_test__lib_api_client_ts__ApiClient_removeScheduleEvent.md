---
node_id: concorda-test::lib/api-client.ts::ApiClient.removeScheduleEvent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e4632a3d03b38e24a711eef3104617121d8b20b1ade324c346b2e188e997ee65
status: current
---

# ApiClient.removeScheduleEvent

## Purpose

Test-harness wrapper for the role-polymorphic "remove from MY schedule" DELETE — the Playwright equivalent of the prod `eventsApi.removeScheduleEvent` (see `dossiers/services/concorda_web__src_lib_api_ts__eventsApi_removeScheduleEvent.md`). Used by 8 specs across `tests/auth/email-link-flows.spec.ts` and `tests/events/event-schedule.spec.ts` to clean up captain plans and bookmarks between assertions so a single test can run multiple add/remove cycles without re-seeding. Future Claude: this is a cleanup verb in test code, but it hits the same role-polymorphic endpoint as prod — calling it as a captain tears down `SailingEvent` + `EventCrew` + crew bookmarks server-side, not just the caller's `PersonEvent`.

## Invariants

- Path is `/api/events/my-schedule/events/{eventId}` — the source event ID, not a `PersonEvent` ID. Server resolves the row by viewer role (bookmark / personal-owner / co-owner-with-SE).
- Return type is `Promise<unknown>` — the wrapper discards the `{ removed, had_plan, crew_removed }` response shape that the prod UI branches on. Specs that need to assert teardown happened must add their own typed call or check via `listMySchedule()`.
- Auth comes from `this.token` set by `login()`; no admin override exists server-side, so the client must be authenticated as the schedule owner.

## Gotchas

- **Not just an unbookmark.** When called by a captain (boat owner with a `SailingEvent` for this event), the server runs `_cleanup_sailing_event`: deletes `EventCrew` rows, fires `event_canceled` calendar emails to invited/accepted/confirmed crew, and pulls those crew members' schedule bookmarks. A "cleanup between tests" call from a captain persona will email real-looking calendar cancels into the test mailer and mutate other personas' schedules.
- The wrapper returns `unknown`, so a spec calling `await client.removeScheduleEvent(id)` and then immediately asserting "event no longer on schedule" via UI will pass even if the server returned `removed: false` (all three fall-through branches missed). If a spec needs that signal, use `rawRequest('DELETE', ...)` and inspect the body.
- 404 only fires when bookmark, personal-owner copy, AND co-owner-SE branches all miss. A captain with no `PersonEvent` but with an `SailingEvent` still removes successfully — don't assume "I never bookmarked it" implies 404.
- No commits on this wrapper specifically have reverted; it landed in `7d14e73 test(lib): extend api client with crew/event invite methods` and has been stable. Risk lives in the prod endpoint it mirrors.

## Cross-cutting concerns

- **Email side effects in tests:** captain-path calls trigger `event_canceled` emails. The test mailer captures these; specs asserting "no cancel email was sent" must scope their assertions or use a non-captain persona for cleanup.
- **Cross-persona cascades:** in the co-owner branch, *other* boat owners' bookmarks for the same event are deleted server-side. A test that seeds two co-owners and removes the event from one will silently affect the other's schedule.
- **Series counterpart:** there is no `removeScheduleSeries` wrapper here yet. Specs that need to clear a series bookmark loop over events and call this per-event, which works but fires N teardowns.

## External consumers

None. This is test-only code — concorda-test is not published or consumed outside its own Playwright runs.

## Open questions

- Should the wrapper return the typed `{ removed, had_plan, crew_removed }` shape so specs can assert on teardown semantics without dropping to `rawRequest`? Today every caller throws the response away.
