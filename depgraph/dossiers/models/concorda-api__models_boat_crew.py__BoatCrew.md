---
node_id: concorda-api::models/boat_crew.py::BoatCrew
node_kind: model
feature: crew-management
last_reviewed: 2026-05-09
last_reviewed_against_hash: 23a3bb330667ec450a258e03fe97d0ec7f2a04778319268fe3639adec6409b68
status: current
---

# BoatCrew

## Purpose

The membership join between a `Boat` and a `Person`. One row per (boat, person) — the `UniqueConstraint("boat_uuid", "person_uuid")` is enforced. Each row carries the person's role on the boat (owner/crew/prospective), their preferred position, lifecycle status (active/prospective/invited/declined), priority order in the owner's invite picks, and an opaque `invite_token` while the invite is outstanding.

This is the table behind every "who's on this boat" view in the system: the crew tab on a boat detail page, the crewfinder roster, the email invite landing page, the race-crew picker. It is also where invite acceptance lands — accepting a `pending` invite creates a BoatCrew row in the same transaction that deletes the `PendingCrewInvite`.

## Invariants

- **One row per (boat, person).** Enforced at the DB layer by the unique constraint. Code that adds crew must check existence first or catch the IntegrityError; do not assume `db.add` succeeds.
- **`status` lifecycle is finite:** `invited` → `active` (via accept) | `declined` (via decline). `active` and `prospective` are terminal-ish states a person can stay in; `invited` and `declined` are transient.
- **`invite_token` is the SHA-256 hash of the raw token, not the raw token.** Same convention as `PendingCrewInvite`. The raw token only ever lives in the email URL.
- **`role` defaults to `"crew"`.** `"owner"` is set explicitly when a coowner invite is accepted; never mass-update role to owner without going through the coowner-invite flow (which creates an approval).
- **`priority` is the order of click in the owner's invite picks** (per memory `project_invite_priority_order`). First click = priority 1. Future cap policies will rank from this; do not silently re-sort.
- **`notes` is owner-visible private metadata.** It's surfaced to the boat owner in the crew picker UI but never to the crew member themselves. Keep that asymmetry — owners use it to remember why they invited someone.

## Gotchas

- **Accepting an invite re-uses the row, doesn't recreate it.** `accept_invite` in `routers/invite.py` does `record.status = "active"; record.invite_token = None`. This preserves `invited_by_uuid`, `notes`, and the original `created_at`. Don't rewrite this to delete-and-recreate — the audit trail depends on row identity.
- **`role: "prospective"` is for crewfinder.** It means "this person has expressed interest but isn't on the active crew." Don't confuse with `status: "prospective"`. The model has both fields and they mean different things.
- **`config_uuid` ties to a `BoatConfig` (per-position assignments).** Nullable because not every boat uses configs. When non-null, it must point to a config that belongs to the same boat — there's no FK to enforce this; route handlers do the check.
- **32 endpoints query BoatCrew.** Adding a column with `nullable=False` and no default will break migrations; always provide a default for legacy rows.

## Cross-cutting concerns

- **Websocket:** Every mutation broadcasts `boat_crew.updated` with the boat id (see `broadcast_event` dossier).
- **Privacy:** Per memory `feedback_crew_visibility_privacy`, peer crew identities are hidden unless the resume is published. Filter at the read site, not the model layer.
- **Approvals:** Coowner invites go through `ApprovalRequest`; once approved, the BoatCrew row's role flips to `owner`.
- **Crew pools:** `CrewPool` is a separate logical grouping; BoatCrew is the concrete roster.

## External consumers

- **Concorda iOS app**: every crew-list screen reads BoatCrew indirectly via API. Renaming a column on this model breaks ML if shipped with old client builds.
- **Test fixtures:** `concorda-test/lib/test-data.ts` references BoatCrew shapes for seeded fixtures.

## Open questions

- Should `status` be an enum at the DB layer? Today it's a String(20) and code defends with `.lower()` checks.
- The `priority` field's intended cap behavior is described in memory but not yet implemented — see `project_invite_priority_order`.
