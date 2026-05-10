---
node_id: concorda-api::models/contact_role.py::ContactRole
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4cc02c30842d715a972800a9a892fe53f851a7ce15245f79be81fe770656f6c2
status: llm_drafted
---

# ContactRole

## Purpose

Backend SQLAlchemy model for polymorphic contact-role assignments. Each row is one `(entity_type, entity_uuid, contact_uuid, role)` tuple — answering questions like "who is the steward / fleet captain / billing contact for this organization?" but also for regattas, series, and events. The Contact itself (name/email/phone) lives in a separate `Contact` table; this table is the join + role-label. As of 2026-05-10 only the organization-scoped CRUD routes consume it (4 dependents in `routers/organizations.py`), but the schema was deliberately built polymorphic so regatta/series/event roles can land without another junction table.

## Invariants
- One row = one role assignment. A single contact can hold multiple roles on the same entity (multiple rows), and the same role can be held by multiple contacts (no uniqueness constraint enforced).
- `entity_type` is constrained by convention only — comment lists `organization, regatta, series, event`. No CHECK constraint; typos will silently create orphan rows.
- `role` is a free-form `VARCHAR(50)`. Known values: `billing_contact, delegate, fleet_captain, rc_chair, pro, race_committee, coordinator`. New roles are added by writing them; no enum table.
- `contact_uuid` references `contacts.id` but there is no FK — deletes of Contact rows will leave dangling ContactRoles.
- `BaseModel` injects `id`, `type='ContactRole'`, `created`, `modified`. The explicit `__init__` sets `type` so polymorphic discriminator queries work.
- Indexes exist on `contact_uuid` and the composite `(entity_type, entity_uuid)` — lookups should filter by both, not just `entity_uuid`.

## Gotchas
- This table replaced four separate junction tables (`organization_contacts`, `regatta_contacts`, `event_contacts`, `series_contacts`) in commit `a61b325` / migration `017`. Anything older than 2026-04-01 referencing those tables is dead — grep before believing old docs.
- The org-contacts routes treat `contact_role_id` as the URL identifier (not `contact_id`), because a contact can hold multiple roles on one org. Don't "simplify" the URL to use contact_id — you'll break the multi-role case.
- `list_org_contacts` does an N+1: one `Contact` query per ContactRole row. Fine at org-admin scale (handful of rows) but don't reuse this pattern for higher-volume entity_types without batching.
- No FK + no cascade means deleting a Contact via any other path leaves stale role rows. There is no cleanup job today.

## Cross-cutting concerns
- All four dependent routes are guarded by `_require_admin` + `_require_org_admin_scope(org_id, current_user)` — only org admins of the matching org can read/write. The model has no row-level auth of its own; it relies on the router scope check.
- No websocket events, no audit log entries on create/update/delete. If billing-contact changes need a paper trail later, this is the layer to add it.
- Side effect on Contact: `POST /organizations/{id}/contacts` creates both a `Contact` and a `ContactRole` in one transaction. `DELETE` removes only the `ContactRole`, never the `Contact` — orphan contacts are intentional (they may be reused).

## External consumers
None known. Only the web admin UI consumes the four org-contacts routes. No scheduled jobs, no webhooks, no Expo app surfaces — billing/fleet/rc-chair data is admin-only at present.

## Open questions
- Should `entity_type` become a real enum (DB CHECK or Python `Enum` column) before regatta/series/event routes land? Easier to tighten now than after junk values exist.
- Are `(entity_type, entity_uuid, contact_uuid, role)` tuples supposed to be unique? Today nothing stops a double-insert of the same fleet_captain assignment.
- When a Contact is deleted, what should happen to its ContactRoles? No FK + no cascade today — needs a decision before there's a "delete contact" route anywhere.
