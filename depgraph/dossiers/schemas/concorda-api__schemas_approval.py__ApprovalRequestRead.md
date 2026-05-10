---
node_id: concorda-api::schemas/approval.py::ApprovalRequestRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 380081fefa9e185b90a99c859e9564a37788580092b7e6297f78c8217ce74317
status: llm_drafted
---

# ApprovalRequestRead

## Purpose

Backend Pydantic read schema for approval requests — the wire shape for `GET /api/approval-requests` (list) and the responses to `POST /create`, `POST /{id}/vote`, `POST /{id}/cancel`. Approval requests are the generic N-of-M sign-off rows that gate state transitions whose authorization can't be expressed as a single role check (co-owner invites, promotions, removals, ownership transfers — registered in `services/approval_types/`). The schema bundles the persisted `ApprovalRequest` columns, the full `votes[]` collection (each an `ApprovalVoteRead`), and three server-populated friendly-label fields (`boat_uuid`, `boat_name`, `requester_name`) so callers don't have to second-fetch boats and persons just to render a card. A future Claude touching it should treat it as the canonical "approval as seen by a member" projection — both the inbox/voter view and the requester/outbox view return this same shape.

## Invariants

- `request_type` matches a registered approval type in `services/approval_types/` (`boat_coowner_invite`, `boat_coowner_promotion`, `boat_coowner_removal`, `boat_ownership_transfer`). Adding a new type means registering it in the dispatcher, not just emitting a new string here.
- `status` is one of `"pending"`, `"approved"`, `"rejected"`, `"expired"`, `"canceled"`. There is no enum on the field — it's a `str` — but the list endpoint silently returns `[]` for any other value passed as a filter.
- `votes` is always present (defaults to `[]`); each entry's `decision` is `"pending"`, `"approved"`, or `"rejected"`. A pending vote means a slot has been seeded but not yet cast.
- `target_state` is a freeform `dict[str, Any]` whose schema is per-`request_type`. Don't pattern-match it generically; consult the registered type spec.
- `boat_uuid`/`boat_name`/`requester_name` are best-effort enrichment populated by `_to_read` in `routers/approvals.py`. They are `None` when the join misses (e.g. orphaned subject row, deleted person) — never raise on absence.

## Gotchas

- **Enrichment fields are not persisted columns** — they're stitched onto the Pydantic model in the router's `_to_read` helper after the ORM query, doing 1–3 extra DB hits per row. Adding fields here without populating them in `_to_read` produces silently-`None` output. Commit `33d2dec feat(coowner-invite): rich emails and approval response labels` introduced these; matching them in templates assumes they're filled.
- **`votes[]` ordering is unspecified.** Pulled via the SQLAlchemy relationship with no `order_by`. Don't index by position; match by `voter_person_uuid`.
- **`resolution_reason` semantics differ from `ApprovalVote.reason`.** On finalize, the *latest rejection's* reason is copied to the request — earlier rejections are lost from this field but still readable from `votes[].reason`. UI showing "why was this rejected" should walk the votes, not just read the request.
- **`from_attributes = True` on both classes.** Construct via `ApprovalRequestRead.model_validate(orm_row)` — never hand-build dicts; you'll forget to populate `votes`.

## Cross-cutting concerns

- **Auth**: every endpoint returning this shape is session-cookie gated via `fetchApiAuthenticated` upstream. The schema itself does no scoping — privacy filtering happens in `list_requests_for_voter`/`_for_requester`/`_for_subject` before serialization.
- **Co-owner invite eligibility lives elsewhere**: per the `coowner::eligibility_at_accept` rule, the invitee's Boat-Owner-membership check fires at `services/approvals.py::cast_vote`, not in this schema or its create-side. A `boat_coowner_invite` `ApprovalRequestRead` can perfectly well represent a request whose invitee currently can't accept it — the read shape is unchanged either way.
- **Notifications**: `_dispatch_notifications` consumes the same fields (`requester_name`, `boat_name`) when rendering transactional emails. Renaming or removing a label field breaks email templates as well as the web UI.
- **No realtime**: shape is poll-only; there's no websocket invalidation when a peer votes. Callers must refetch.

## External consumers

None known. Members-only endpoint surface; the Expo iOS app does not consume approvals as of this writing. No documented public API.

## Open questions

- Should the enrichment fields move into a typed sub-object (e.g. `subject: {kind, uuid, label}`) instead of three flat optionals? Today only `boat_*` is wired; co-owner promotion/removal/transfer all share the same boat subject, but a future non-boat approval type would need parallel `event_*` / `org_*` fields and the schema gets wide fast.
- Should `status` be a `Literal[...]` rather than a bare `str`? Tightening it would surface bad filter values at parse time but break forward-compat if a new status (e.g. `"superseded"`) is added.
- Should the response include a TTL hint for pending requests so the UI can warn before `sweep_expired` finalizes? Currently `expires_at` is exposed but no countdown semantics are implied.
