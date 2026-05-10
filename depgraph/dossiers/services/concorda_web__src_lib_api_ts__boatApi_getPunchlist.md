---
node_id: concorda-web::src/lib/api.ts::boatApi.getPunchlist
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c4f598a1135eeb2e3d13c66278fb95b8e8dc09beb965aa56f3327a0b2defc7e4
status: current
---

# boatApi.getPunchlist

## Purpose

Client-side mirror for the boat's punchlist — the per-boat todo list of maintenance/repair items (e.g. "replace windex," "wax hull"). `boatApi.getPunchlist(boatId)` is a thin GET wrapper around `/api/boats/{boatId}/punchlist` returning `PunchlistItem[]`. It pairs with `createPunchlistItem` / `updatePunchlistItem` / `deletePunchlistItem` to round out the CRUD surface. Four call sites consume it: `BoatInline` (boat-detail panel for owners), `BoatOwnerView` (full owner view), and twice from `CrewBoatInline` (the crew-side dashboard tile renders a count and a preview list, hence two `useQuery` calls in one component). A future Claude editing this should treat it as the canonical fetch path — there is no separate detail endpoint, the list is the source of truth and the editor UIs filter/group client-side.

## Invariants

- Endpoint shape is `/api/boats/{boatId}/punchlist` (no trailing slash, plural "boats"). The three sibling mutators share this prefix; keep them in lockstep.
- Returns `PunchlistItem[]` ordered by `created DESC` server-side — do not re-sort defensively on the client unless you also update consumers that rely on newest-first.
- Auth: backend requires `_require_crew_or_owner` (any active `BoatCrew` row, not just role=owner). Despite the "owner-readable" framing in some UI copy, **active crew members can read and create/update items** — only delete is gated to creator-or-owner.
- `PunchlistItem.importance` and `.status` are free-form strings on the wire; UIs assume `high|medium|low` and `open|in_progress|done` respectively. No enum is enforced server-side.
- `created_by_name` / `assigned_to_name` are server-resolved convenience fields — don't try to derive them from a separate person fetch on the client.

## Gotchas

- `CrewBoatInline` calls `getPunchlist` twice (lines 42 and 62 in that file). React Query will dedupe by key, so both should use the same `["punchlist", boatId]` key — if you change one call signature, audit both, or you'll get a duplicate network request and a stale-list bug.
- The recent commit log on `api.ts` is dominated by crew/coowner/schedule churn (`bf44b09`, `47688ac`, `eb382d2`, `9e1cc53`); the punchlist endpoints themselves have been quiet, which means there is **no recent battle-testing** — assume edge cases (e.g. orphaned `assigned_to_uuid` after a crew removal) are unverified.
- Backend broadcasts `PUNCHLIST_UPDATED` on create/update/delete via `broadcast_event(PUNCHLIST_UPDATED, boat_id)`, but `getPunchlist` itself does not subscribe to that channel. If you want live updates in a consumer, wire the websocket listener at the component layer and invalidate the React Query key — don't push that into the service wrapper.
- Delete returns `{message: string}`, not the deleted item. The TS type reflects this; callers that optimistically remove from a cached list must do so themselves.

## Cross-cutting concerns

- **Auth:** routed through `fetchApiAuthenticated`, which attaches the bearer token and 401-redirects on expiry. No public read path exists.
- **Websocket:** mutations broadcast `PUNCHLIST_UPDATED` keyed on `boat_id` — relevant if you add a punchlist surface to dashboard tiles that should refresh when other crew edit.
- **Audit:** none. Punchlist edits are not currently captured by the audit/approvals system.
- **Permissions split:** read/create/update = any active crew; delete = creator or owner. UI must mirror this — surfacing a delete affordance to non-creator non-owner crew will 403.

## External consumers

None known. No mobile/Expo consumer of the punchlist endpoint as of this writing; iOS app currently focuses on schedule/crew flows. No webhooks, no scheduled jobs, no public API.

## Open questions

- Should `importance`/`status` become enums (DB-level CHECK or Pydantic Literal)? Today they're free strings, which means a typo silently sticks.
- Does deletion need a soft-delete / audit trail? Currently a hard `db.delete` — no recovery if a crew member nukes a real maintenance item.
- Is "any active crew can edit" the desired policy long-term, or should boat owners be able to lock items (e.g. when assigned)?
