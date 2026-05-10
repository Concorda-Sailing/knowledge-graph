---
node_id: concorda-test::lib/api-client.ts::ApiClient.getEventCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 91433a2e74e064a24562019835549fe71f75815d8137db6dfe5133b1c6d9ac74
status: current
---

# ApiClient.getEventCrew

## Purpose

Test-harness wrapper for `GET /api/events/{event_id}/sailing-event/crew` — the `ApiClient` method that Playwright specs use to assert event crew state after pool/invite/respond mutations. Mirrors prod `eventsApi.getEventCrew` (see `concorda_web__src_lib_api_ts__eventsApi_getEventCrew.md`) but with a stripped-down inline return type — only `person_uuid`, `status`, and `position_name` are surfaced; the full PII-gated `EventCrewRead` shape is not modeled here because tests don't assert on PII masking from this seam. Used across 2 spec files (`tests/auth/email-link-flows.spec.ts`, `tests/boats/coowner-shared-events.spec.ts`) and roughly 7 tests, always under the same pattern: drive a mutation (UI navigation, emailed accept/decline link, or another API call), then `getEventCrew(eventId).find(r => r.person_uuid === X)` and assert `.status` is `invited`/`accepted`/`declined`.

## Invariants

- Returned shape is `Array<{ person_uuid, status, position_name? }>`. The full prod `EventCrewRead` includes role, PII fields, `resume_published`, `responded_by_uuid`, etc.; specs ignore all of those. A prod-side rename of `person_uuid` would break every consumer silently — only the inline type guards it.
- Caller must be **captain or crew on the SailingEvent** for `event_id`; the route 404s otherwise. Specs read as the boat-owner persona (Bob, or Dan when Dan owns the event) — read-as-Bob immediately after mutating-as-Carol is the standard pattern; forgetting `setToken(bobToken)` is the typical flake mode.
- Status values the suite asserts on: `invited`, `accepted`, `declined`. `pool`, `confirmed`, and `requested` exist in the prod enum but aren't currently asserted by these specs.

## Gotchas

- `ApiClient` carries a single token; intervening `login()` / UI-driven mutations reassign it. The accept-link tests in `email-link-flows.spec.ts:177,198` and the request-flow tests at `:421,468` all do `api.setToken(bobToken)` immediately before `getEventCrew` to flip back to the captain identity after walking the recipient through the UI. Don't refactor those `setToken` lines out.
- The shared-test host is long-lived (`test.mbs`, 10.0.1.140) and the DB is **not** wiped between specs. Each test cleans up via `removeScheduleEvent(eventId)` after asserting; if that fails, the next run inherits a stale EventCrew row and the assertion still passes for the wrong reason. Don't rely on `getEventCrew` to detect leakage — inspect by event id, not by person.
- The inline return type is hand-mirrored, not imported from prod. Recent commit on the prod side changed `EventCrewStatus` from `string` to a literal union (`bf44b09`) — that change did **not** propagate here; this stub still types `status` as bare `string`. Acceptable for assertion code, but a typo like `expect(...).toBe('peding')` will compile.
- Self-signed TLS is bypassed process-wide via `NODE_TLS_REJECT_UNAUTHORIZED=0` at `api-client.ts:9`. Acceptable here, but means this client must never be repurposed against staging/prod.

## Cross-cutting concerns

- **Auth**: bearer token via `Authorization: Bearer <jwt>` set by `login()` or `setToken()`. No cookie/session — independent of the Playwright UI session lifecycle, which is why specs can drive UI as one persona and read API state as another via `setToken` toggles on the same client.
- **No websocket awareness**: specs use direct `getEventCrew` reads after a mutation rather than subscribing to `event_crew.updated`. Reads are immediate, not `expect.poll`-wrapped, because the mutation endpoints already complete synchronously.
- **PII gating**: the prod endpoint applies `rule::crew_visibility::peer_pii_resume_gated`. This wrapper sees the masked shape but doesn't expose the masked fields, so PII assertions cannot be made through this method — a future "peer can/can't see PII" test would need a fuller return type.

## External consumers

None. This is internal to the `concorda-test` Playwright suite.

## Open questions

- Worth widening the inline return type to include `role`, `resume_published`, and the optional PII fields so future PII-visibility specs can assert through the same seam? Right now they'd have to add a sibling method or use `rawRequest`.
- The 7+ call sites all do `.find(r => r.person_uuid === X)?.status` — promotable into an `ApiClient.getEventCrewStatus(eventId, personUuid)` helper that returns `string | undefined`?
