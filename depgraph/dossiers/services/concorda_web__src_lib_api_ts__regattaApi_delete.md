---
node_id: concorda-web::src/lib/api.ts::regattaApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 25305f9adaae7ad8b850e72a605ebe141684ceb3e1fc10af16cd3e44b8bd01d3
status: current
---

# regattaApi.delete

## Purpose
Client-side mirror for admin-side hard-deletion of a Regatta (race) record via `DELETE /api/regattas/{id}`. Used by event managers and org admins to permanently remove a race from the catalog when it was created in error, duplicated, or cancelled outright. The handler is a plain `db.delete(regatta); db.commit()` — no soft-delete, no archive flag — so a future Claude making a "remove race" decision should treat this as destructive and irreversible from the UI side.

## Invariants
- Caller must hold `event_manager`, `org_admin`, or `system_admin` (the `_require_manager` dependency on the route).
- Org-scope is enforced via `_require_regatta_org_scope`: a manager in org A cannot delete a regatta scoped to org B even though the role check passes.
- Returns 204 on success, 404 if the regatta id doesn't exist; the client `fetchApiAuthenticated<void>` resolves to undefined and consumers chain a `toast({title: "Deleted"})` + navigate/refresh.
- Slug uniqueness is freed: the deleted row's `slug` becomes available for reuse on the next create (no tombstone).

## Gotchas
- The `Regatta` SQLAlchemy model declares **no `relationship()` and no `ondelete` cascades** — `series_uuid`, `region_uuid`, `oa_uuid` and the regatta-side of `OrganizationRegatta`, `PersonRegatta`, `RegattaIntent`, `RegattaDocument`, and `Event.regatta_id` are loose `String(36)` columns with no FK enforcement. Deleting a regatta will silently leave dangling rows in those tables. The framing "Cascades: removes EventRegistrations, Series associations, etc." is **not actually true at the DB layer** — anyone relying on cleanup must add it to `delete_regatta` explicitly.
- `Event.regatta_id` pointing at the deleted regatta becomes a dangling reference; calendar/event lookups that join through it must tolerate nulls/missing rows.
- All three call sites unconditionally call `regattaApi.delete` without confirming the regatta has zero accepted crew, zero registrations, or zero series-membership — UX is a single `DeleteConfirmDialog` with no impact preview. Compare to `seriesApi.delete` (the adjacent dossier) before assuming symmetric semantics.
- `races/[id]` page calls `router.push("/members/admin/events/races")` after delete; `races/page.tsx` calls `load()` to refetch the list; `series/[id]` calls `await load()` to refresh the series view. Three different post-delete behaviors — keep them aligned if you change the response shape.

## Cross-cutting concerns
- **Auth**: managers only, org-scoped (see invariants).
- **Audit**: none on the delete path — no audit-log write, no event published. If audit becomes a requirement for destructive admin actions, this is a gap.
- **Websocket/realtime**: no broadcast. Other clients viewing the regatta will 404 on next fetch.
- **Side effects on other features**: schedule cards, calendar entries, and series detail pages that reference the regatta via id will silently lose the link; series-editor `load()` masks this locally but other surfaces won't refresh.
- **Rate limits**: standard authenticated route, no special limiter.

## External consumers
None known. No webhooks, scheduled jobs, or Expo app calls observed against `DELETE /api/regattas/{id}` — this is admin-web-only today.

## Open questions
- Should this become a soft-delete or refuse-when-referenced operation, given the lack of FK cascades and the silent-orphan risk?
- Should the delete endpoint return a structured impact summary (events touched, registrations dropped, series memberships removed) so the confirm dialog can warn the operator?
