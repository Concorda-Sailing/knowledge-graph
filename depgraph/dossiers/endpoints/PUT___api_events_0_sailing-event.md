---
node_id: PUT::/api/events/{0}/sailing-event
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ab3b4ea458d0130098e5778dd9e5654a73065100abdfc4d23342a87d2a6949d7
status: current
---

# PUT /api/events/{event_id}/sailing-event

## Purpose
Endpoint handler for owner-side per-boat `SailingEvent` upsert — backend partner of `eventsApi.upsertSailingEvent`. The route URL is event-scoped (`PUT /api/events/{event_id}/sailing-event`) but the handler resolves WHICH `SailingEvent` row to touch by joining `SailingEvent` → `BoatCrew` filtered to `(person_uuid=caller, role="owner", status="active")`. This caller-scoped lookup is the load-bearing design choice: multiple captains can each have their own SE on a single Event, and an unscoped `event_uuid`-only lookup would silently overwrite a stranger's race plan. The handler also enforces the captain↔boat ownership chain on writes, validates that any `crew_pool_id` belongs to the same boat, computes a calendar-email diff against pre-update field values, and dispatches `logistics_set` / `logistics_updated` / `event_canceled` `.ics` mails to the active roster as a non-fatal side effect.

## Invariants
- Caller-scoping is non-negotiable: the SE-to-touch is found by joining through owner-role `BoatCrew`, never by `event_uuid` alone.
- Creating a brand-new SE requires `boat_uuid` in the payload (anti-orphan guard at line 1979) — 400 otherwise.
- When `boat_uuid` is set or changed, the caller must own that boat (`role="owner"`, `status="active"`) — enforced via `_require_boat_owner`, 403 otherwise.
- A non-null `crew_pool_id` must reference a `CrewPool` whose `boat_uuid` matches the SE's resolved boat — 400 otherwise.
- `model_dump(exclude_unset=True)` semantics: omitted fields are not touched; explicit `null` clears them. The handler does not re-impose defaults.
- The single `db.commit()` at the end covers SE create/update AND any email-send side effects' DB reads — but the email sender is wrapped in `try/except Exception: pass` so a failed email never rolls back the upsert.

## Gotchas
- `8842b8d fix(schedule): suppress Crew badge when captaining own boat for the race` — this endpoint is the only path that turns a crew bookmark into captaincy. The web client's schedule detail page intentionally skips a "bare boat_uuid" auto-upsert for crew-viewers because doing so here would create their first owner-side SE and silently promote them.
- `6c314f5 fix(calendar): render .ics + email body in the org timezone, not UTC` — the email helper renders times via the org's TZ, but this handler stores naive-UTC `dock_time`/`arrival_time`/`departure_time` (UtcDateTime convention). Don't pre-convert before assigning.
- The `_watched` snapshot is taken BEFORE `db.add(se)` and BEFORE the field-by-field copy. Adding a new logistics-bearing field to `SailingEventUpsert` requires also adding it to `_watched` or it won't trigger `logistics_updated` emails — silent failure.
- `cal_kind` selection is order-sensitive: `(has_dock and not had_dock)` wins over `(has_dock and had_dock and any-changed)`. A first-time dock_time set on an SE that previously had logistics fields ALL produces `logistics_set`, not `logistics_updated`.
- `dd72f2f feat(crew): EventCrewStatus enum, route writes through it` — the `["invited", "accepted", "confirmed"]` filter is currently a string-list literal here; if/when this list narrows or the enum gains values (e.g., `tentative`), update the email-recipient filter or pool/declined crew will start receiving (or stop receiving) calendar mails unintentionally.
- The `_require_boat_owner` short-circuit `(not se or new_boat_uuid != se.boat_uuid)` means re-sending the same `boat_uuid` on an existing SE skips re-authorization. Fine today (ownership can't be revoked mid-request) but worth knowing if BoatCrew row deletion ever becomes async.

## Cross-cutting concerns
- Auth: `require_auth` plus implicit caller-scoping by `BoatCrew.role="owner"` plus explicit `_require_boat_owner` on boat changes.
- Side effect: `.ics` calendar email dispatch (`logistics_set` / `logistics_updated` / `event_canceled`) to active roster (`invited`/`accepted`/`confirmed` only — pool candidates and declined skipped). Email failures are swallowed.
- Transaction: single `db.commit()` after SE write and email loop. No explicit savepoint around emails — relies on the `try/except` in the loop.
- No websocket broadcast; clients re-fetch (schedule detail page) or rely on parent-component reload (event-plan-panel).
- Audit: none beyond standard request logging. The `prev_values` diff is computed only to gate emails; it is not persisted as an event log row.
- No rate limiter (`auth.py`'s in-memory limiter doesn't cover this route).

## External consumers
None known. Three direct callers, all in-tree:
- `concorda-web::src/lib/api.ts::eventsApi.upsertSailingEvent` — primary web client (owner plan editor + schedule detail auto-persist shim).
- `concorda-test::lib/api-client.ts::ApiClient.upsertSailingEvent` — Playwright suite full-payload path.
- `concorda-test::lib/api-client.ts::ApiClient.attachBoatToSailingEvent` — Playwright suite bare-`{boat_uuid}` path mirroring the web shim.

## Open questions
- Should the bare-`boat_uuid` shim path get its own dedicated endpoint (e.g., `POST /api/events/{id}/attach-boat`) so the auto-persist on schedule load can't accidentally fire a logistics email if a captain adds defaults via `BoatConfig` inheritance and a `dock_time` materializes on the new SE?
- `crew_group_priority` is in `SailingEventUpsert` but not surfaced in either web consumer post-consolidated-crew-card — should the field be removed from the schema or repurposed?
- Should the email-dispatch loop move into a background queue / on-commit hook so the request latency doesn't scale linearly with active-crew count, and so `logistics_updated` emails can be debounced when a captain saves twice in quick succession?
