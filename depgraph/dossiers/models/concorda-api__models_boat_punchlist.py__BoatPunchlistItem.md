---
node_id: concorda-api::models/boat_punchlist.py::BoatPunchlistItem
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: af1b66e3756bb839c66760f32f374930b2a87cfa902a9cce0df7507d7ba5d82e
status: current
---

# BoatPunchlistItem

## Purpose

Backend SQLAlchemy model for a single boat-punchlist item — the per-boat todo list of maintenance/repair tasks (e.g. "replace windex," "wax hull"). Boat-scoped via `boat_uuid` (indexed, no FK constraint enforced at the model layer), free-string `importance` and `status` fields with UI-conventional defaults (`medium` / `open`), and two person-uuid pointers: `created_by_uuid` (required, set from `current_user.id` at create time) and `assigned_to_uuid` (optional). Inherits `id` / `type` / `created` / `modified` from `BaseModel`. This is the row that `PunchlistItemRead` serializes and that `boatApi.getPunchlist` ultimately fetches; there is no detail endpoint, so this table is the source of truth and consumers filter/group client-side.

## Invariants

- `boat_uuid` is non-null and indexed but **not** a FK — orphaned items after a boat delete are possible if the boat-delete path doesn't cascade (verify before relying on referential integrity).
- `created_by_uuid` is non-null; the router always sets it from `current_user.id`. Don't expose it on `PunchlistItemCreate` — it is server-set.
- `importance` is `String(10)`; `status` is `String(20)`. UI conventions are `high|medium|low` and `open|in_progress|done`. Neither is enforced at the DB or Pydantic layer — a typo writes through.
- `__init__` hard-codes `type="BoatPunchlistItem"`. Don't bypass it with `BaseModel.__init__` directly or you'll get a NULL-type insert failure.
- `created` / `modified` are naive-UTC per the project-wide `UtcDateTime` convention; `due_by` is `DateTime` (no tz) and should be treated the same way.

## Gotchas

- The model has no SQLAlchemy `relationship()` for `created_by_uuid` or `assigned_to_uuid` — the join-name fields on `PunchlistItemRead` are filled by `_punchlist_to_read` (routers/boats.py:100) via an explicit `Person` query. Adding `relationship()` here would let `from_attributes` populate them automatically but would change query semantics; don't do it without auditing the helper.
- No constraint that `assigned_to_uuid` points at someone currently on `BoatCrew` for this boat. A crew removal leaves a dangling assignment and the read silently shows blank name.
- Only two commits touch this file (`ee82e42` schema redesign, `a88ee0d` initial boat setup). There has been **no recent fix/revert cycle** — assume edge cases are unverified.
- Delete is a hard `db.delete` — no soft-delete, no audit trail. A crew member with creator-rights can nuke a real maintenance item with no recovery path.

## Cross-cutting concerns

- **Auth:** read/create/update gated to any active `BoatCrew` row via `_require_crew_or_owner`; delete narrows to creator-or-owner. The model itself enforces nothing — all policy lives in the router.
- **Websocket:** all three mutating endpoints call `broadcast_event(PUNCHLIST_UPDATED, boat_id)` after commit. Any new mutation path on this model must broadcast or consumer caches will go stale.
- **Audit:** none. Punchlist mutations are not captured by the audit/approvals system; `created` / `modified` are the only forensic trail.
- **PII surface:** `created_by_uuid` / `assigned_to_uuid` are resolved to first+last names in the read schema and exposed to any active crew reader.

## External consumers

None known. No Expo/iOS surface, no webhooks, no scheduled jobs, no public API. Web client is the sole consumer via `boatApi.getPunchlist` and its three CRUD siblings.

## Open questions

- Should `importance` / `status` become DB-level CHECK constraints or be promoted to enums? Free strings silently mis-bucket on typo.
- Should `boat_uuid` get a real FK with `ON DELETE CASCADE`? Today nothing in the model layer guards against orphaned rows.
- Should `assigned_to_uuid` be referentially validated against current `BoatCrew` membership at write time, or is "any Person" intentional (e.g. for assigning a yard/service contact)?
