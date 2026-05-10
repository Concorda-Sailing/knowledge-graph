---
node_id: concorda-api::models/crew_pool.py::CrewPool
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f5c7d7ac1c621a3bca9d4f9f6a63f5ef95c86ffd7748cf44e9953d5e89a86404
status: llm_drafted
---

# CrewPool

## Purpose
Backend SQLAlchemy model for a named crew grouping attached to a boat (e.g. "My Distance Crew", "Wednesday Night Crew"). A `CrewPool` is the concrete persistence behind boat-owners' reusable crew rosters: the owner picks members once, then bulk-invites that pool when scheduling regattas, series, or one-off sailing events. Distinct from the user-facing "My Crew" concept — My Crew is a person-owned logical grouping (sailors I crew with), whereas `CrewPool` is boat-scoped (the crew *for this boat*). Future Claudes editing this should preserve that boundary: pools belong to a boat, not a captain.

## Invariants
- `boat_uuid` is required and indexed; every pool belongs to exactly one boat.
- `member_ids` is a JSON list of person UUIDs whose **order is priority-significant** — index 0 is priority 1, index 1 is priority 2, etc. Reordering is a semantic change, not cosmetic. Invite dispatch reads this order when sending crew invites.
- `name` is required, max 100 chars; uniqueness is not enforced at the DB level (callers / routers police duplicates if needed).
- `is_default` marks the boat's default pool; at most one default per boat is the expected business rule (not enforced by schema — caller responsibility).
- `type="CrewPool"` is forced in `__init__` for the BaseModel discriminator; do not override.

## Gotchas
- **Scope was reversed on 2026-05-03 (commit 770d190): pools used to be person-scoped, now they are boat-scoped.** Any code or memory that still treats pools as "my pools" rather than "this boat's pools" is stale. Look for lingering `person_uuid`/`owner_uuid` lookups in callers.
- `member_ids` is a raw JSON list, not a relationship — there is no FK enforcement. Deleting a person does *not* cascade; stale UUIDs can sit in the list. Callers that render members must tolerate missing persons.
- Order matters (see Invariants). A naive "set-equality" diff on `member_ids` will silently drop priority changes. Updates should compare lists positionally.
- No `organization_id` column — scoping to org goes through `boat_uuid -> Boat.organization_id`. Don't add per-org filters here directly.
- Only two commits in history (770d190 reversal, 1118209 introduction); the model is young and conventions are still settling.

## Cross-cutting concerns
- **Routers (7 dependents):** CRUD lives at `/api/profile/boats/{boat_uuid}/crew-pools[...]`; consumption lives in `/api/events/my-schedule/add-regattas`, `/add-series`, and `PUT /api/events/{id}/sailing-event` — those endpoints read pools to bulk-create `EventCrewInvite` rows, preserving `member_ids` order as invite priority.
- **Auth:** boat-owner / boat-manager only for mutations; consumption endpoints additionally require the caller own the target event/regatta. No row-level filter on the model itself — auth is router-side.
- **No audit, no websocket, no rate limit** specific to this model.
- **Side effect:** changing `member_ids` does not retroactively rewrite already-sent `EventCrewInvite` priorities — it only affects future invite dispatches.

## External consumers
None known. Web UI (`profileApi.listCrewPools`) and Expo app are the only readers; no webhooks, scheduled jobs, or third-party integrations consume this model.

## Open questions
- Should `is_default` be enforced as at-most-one-per-boat at the schema level (partial unique index)?
- Should deleting a person trigger cleanup of their UUID from every pool's `member_ids`, or is lazy filtering at read time the intended contract?
- When a boat is transferred to a new owner, do pools follow the boat (current behavior, since they're boat-scoped) or should some be archived? Not yet exercised in production.
