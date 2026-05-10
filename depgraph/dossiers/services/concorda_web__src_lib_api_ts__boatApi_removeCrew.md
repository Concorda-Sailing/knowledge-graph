---
node_id: concorda-web::src/lib/api.ts::boatApi.removeCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d295f966a6a2ccade23c9bbe3e4566b48f35e6a4ad97229779332f2554f065f8
status: current
---

# boatApi.removeCrew

## Purpose
Client-side mirror for an owner removing a crew member from their boat's BoatCrew list (`DELETE /api/boats/{boat_id}/crew/{crew_id}`). This is a **permanent removal of the BoatCrew row**, not a status change — once called, the row is gone and any history attached to it disappears. The endpoint is overloaded: the same `crew_id` path slot also matches a `PendingCrewInvite` row (email-only, person doesn't yet exist), so the server tries `BoatCrew` first and falls back to `PendingCrewInvite`. Future Claude: pick this when the owner action is "make this person no longer crew on this boat" (active, invited-but-not-accepted, prospective application decline, or pending email-invite cancel). Do NOT use it for status flips like decline-while-keeping-relationship — use `updateCrew` for that. Four call sites consume it: `BoatCrewTable.handleRemove` (active-roster removal w/ confirm dialog), and three handlers in `MyCrewTab` (`handleDeclineApplication`, `handleRemovePendingInvite`, `handleRemoveInvite`) covering applications, email-only pending invites, and named-person invited-state cancellations respectively.

## Invariants
- Owner-only: server enforces `_require_owner`; non-owner callers get 403. UI must hide/disable the action for non-owners (passes `isOwner` prop).
- Cannot self-remove as owner: server returns 400 if `crew.role == "owner" and crew.person_uuid == current_user.id`. UI should not offer the action on the owner row.
- The `crew_id` argument is polymorphic — it's either a `BoatCrew.id` or a `PendingCrewInvite.id`. Callers do not need to know which; the server resolves it. Both code paths broadcast `BOAT_CREW_UPDATED` and return `{message: ...}` (different message strings).
- 404 if neither table has a matching row scoped to the boat. Callers must `onRefresh()`/`fetchData()` after success because the server returns no entity.

## Gotchas
- **Permanent delete, not soft-delete.** No `deleted_at`, no audit row, no restore path. Recent commits added invite resends and direct-accept links but `remove_crew` itself has not been softened — once removed, re-adding requires a new invite cycle.
- The "decline application" path (`my-crew-tab.tsx:211`) deletes the prospective BoatCrew row outright. There is no "declined" tombstone, so the same person can immediately re-apply. If product wants application throttling, that must live elsewhere.
- Pending-invite cancellation (`my-crew-tab.tsx:260`) and named-person invite cancellation (`my-crew-tab.tsx:273`) hit the same endpoint with different ID kinds. The toast copy distinguishes them; the API does not.
- Tier-A/B IDOR audits (`c9a7c41`, `8971b1c`) tightened authz around boat-crew endpoints — don't loosen `_require_owner` here without re-checking those audits.
- **Future-requirement (per `project_my_crew_delete_guard`):** removal from My Crew should warn-and-cascade when the target has open invites or accepted slots on upcoming events. Current implementation does neither — it just deletes the BoatCrew row, leaving any `EventCrew`/invite rows referencing the same person dangling or orphaned. The guard is unimplemented on both client and server; design choice (warn-only vs. cascade-delete vs. block) is open.

## Cross-cutting concerns
- **Auth:** session cookie via `fetchApiAuthenticated`; server `require_auth` + `_require_owner`.
- **Realtime:** server emits `BOAT_CREW_UPDATED` SSE/websocket event scoped to `boat_id` on success. Subscribers (boat-crew-table, my-crew-tab, anything listening to BOAT_CREW_UPDATED) should re-fetch automatically; explicit `onRefresh()`/`fetchData()` calls are belt-and-suspenders.
- **Side effects on other features:** an active crew member removed here may still be referenced by EventCrew rows, crew-pool memberships (`profileApi.updateCrewPool`'s `member_ids`), and potentially open invites. None of those are cleaned up server-side. The My Crew delete guard is the planned answer.
- **No rate limiting** beyond global auth limits; owner-only authz is the gate.

## External consumers
None known. This is a member-facing UI action only; not exposed to the iOS app surface yet, no webhooks, no scheduled jobs.

## Open questions
- Should the My Crew delete guard be enforced server-side (refuse with 409 + cascade hints) or client-side (preflight check + confirm dialog)? Memory note suggests warn-and-cascade UX, which implies client-side preflight using existing endpoints.
- Should "decline application" be a status flip (`status="declined"`) instead of a row delete, so re-applications can be rate-limited and history preserved?
- Pending-invite cancellation reuses the same endpoint as crew removal — is that conflation worth keeping, or should pending invites get their own DELETE route for clearer telemetry?
