---
node_id: concorda-test::lib/api-client.ts::ApiClient.setEventCrewPool
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a4102315e57b853502a96df2adf4c021117dad939353d8c41401c9758600113d
status: llm_drafted
---

# ApiClient.setEventCrewPool

## Purpose
Test-harness wrapper for `PUT /api/events/{event_id}/sailing-event/crew-pool` — sets the candidate crew pool in click/priority order. Three specs use it to seed pool state before exercising invite flows so they don't have to drive the captain UI's crew-picker by hand. Signature `setEventCrewPool(eventId, personUuids[])`; the array index encodes priority (index 0 = priority 1 — see `feedback_invite_priority_order`). PUT semantics — replaces the pool wholesale; no append/remove variant. The standard seed sequence is `login → createSailingEvent → setEventCrewPool → sendEventCrewInvites`, and the order of the `personUuids` array is the load-bearing input that downstream invite-cap policies will key off of.

## Invariants
- `eventId` is the parent `Event` UUID, not the `SailingEvent` UUID — backend resolves the SE via the caller-owned-boat join (same scoping as `upsertSailingEvent`).
- `personUuids` order is the contract. Specs that rely on a specific invite order MUST pre-sort before passing; the wrapper does not sort.
- Caller must be logged in as the boat owner / event manager for the SE — backend returns 403 otherwise and `request()` throws.
- Wrapper returns `Promise<unknown>`; specs should not assert on the response body. Re-fetch via `getEventCrew()` to verify the post-state.
- Empty array clears the pool. Idempotent on identical input.

## Gotchas
- This is the **pool** (candidate set), not the **invite list**. `sendEventCrewInvites()` is the separate step that actually transitions pool rows to `invited` and emails people. Calling `setEventCrewPool` does not notify anyone.
- No client-side validation of UUIDs — server rejects unknown person UUIDs with 400. A spec passing a typo gets a confusing API failure, not a typed error.
- The prod-side endpoint enforces `crew_pool_id` ↔ `boat_uuid` agreement on adjacent endpoints; this wrapper does not interact with that, but if a spec sets the pool and then changes the SE's boat, the pool will refer to people the new boat may not "know" — re-set the pool after a boat change.
- `setToken` discipline applies — the pool is written under the bearer's identity. Forgetting to switch back to the captain after a recipient-side `login()` is the typical flake mode.

## Cross-cutting concerns
- Auth: bearer token via `setToken`/`login`; backend gates by event-owner relation.
- Side effects: writes a `crew_pool` row + member rows server-side; no email/websocket/audit.
- TLS: process-wide `NODE_TLS_REJECT_UNAUTHORIZED=0` from the module's top — fine for the self-signed test host, never repurpose against staging/prod.

## External consumers
None. Test-harness only. Three Playwright specs use it to stage pool state before invite assertions.

## Open questions
- Worth widening the wrapper return type to `{ pool_id, member_uuids[] }` so a spec can assert directly on the persisted order rather than re-fetching via `getEventCrew`? Three call sites today all rely on UI/`getEventCrew` to verify; surface this if pool-priority assertions become first-class.
