---
node_id: concorda-api::schemas/event_crew.py::EventCrewRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1f2e7580d4351bf2db95c23d28162a4296aa32c560c9557c71b010c7f8e076a9
status: current
---

# EventCrewRead

## Purpose

`EventCrewRead` is the FastAPI response schema for every endpoint that returns an EventCrew row — 10 routes covering listing, invite, respond, assign, mark-response, position update, pool set, request, and request-decision. As of `dd72f2f` (today), it is the **response-validation chokepoint for the canonical 6-state status enum and 2-state role enum**: typing `status: EventCrewStatus` and `role: EventCrewRole` makes Pydantic raise on any value outside the canonical set, even though the underlying `String(20)` column has no DB-level constraint. This schema is also the **PII null-masking surface** — fields `person_first_name`, `person_last_name`, `person_picture_url`, `person_email` are populated or nulled by `routers/events.py::_event_crew_to_read(..., include_pii=...)` per the peer-visibility decision in `services/visibility.py::peer_can_see_pii`. If you're adding a field to the EventCrew response, this is the only place to add it; if you're tightening or relaxing what gets returned, you change the dict shape in `_event_crew_to_read` and the type here in lockstep.

## Invariants

- **`status: EventCrewStatus`** — response payload must be one of `pool | invited | accepted | declined | confirmed | requested`. A row that somehow holds a malformed status (raw SQL write, broken import) will 500 here rather than ship. This is the runtime enforcement claimed by `rule::event_crew::status_enum`.
- **`role: EventCrewRole`** — must be `main` or `alternate`. Default is `EventCrewRole.MAIN` so legacy rows missing the field round-trip cleanly.
- **`from_attributes = True`** — the schema is filled from the dict returned by `_event_crew_to_read`, not the ORM row directly. The dict shape and this schema must stay aligned key-for-key.
- **PII fields are `Optional[str] = None`** — required, because the null-mask path sets them to None for peer viewers without a published resume. Making any of `person_first_name`/`_last_name`/`_picture_url`/`_email` non-optional would break the privacy gate.
- **`resume_published: bool`** — always populated by `has_published_resume(person)`; default `False` covers the missing-person case.

## Gotchas

- **Today's `dd72f2f` is fresh** — the enum typing on `status`/`role` landed only this morning. Before this commit these were bare `str`; any caller / test relying on receiving a non-canonical status string (e.g. an obsolete `"pending"` from old data) will now hit a Pydantic ValidationError on the response. Watch for that surfacing in CI before flagging as a regression.
- **The DB column is still `String(20)` with no CHECK constraint** — see EventCrew model dossier. This schema is currently the *only* line of defense between malformed data and clients. Tightening the column is deferred but pending.
- **Reads/filters in routers are still bare strings** — the `dd72f2f` commit only converted *writes* to enum members. Comparisons like `ec.status == "invited"` still work because `EventCrewStatus(str, Enum)` makes `EventCrewStatus.INVITED == "invited"` true, but don't be surprised that the codebase is mixed.
- **`_event_crew_to_read` uses `getattr(ec, "role", "main")` and `getattr(ec, "responded_by_uuid", None)`** — defensive code for partially-loaded rows. If you remove the getattrs assuming the columns are always present, you may break test fixtures or migration-in-progress paths.
- **PII null-masking lives in the router, not the schema** — Pydantic doesn't know about the viewer. The `include_pii` decision is made at the call site by `peer_can_see_pii(...)`. Adding a new PII-ish field requires adding it to *both* the schema (as `Optional`) AND the null-mask branch in `_event_crew_to_read`. Forgetting the null-mask leaks identity; forgetting the schema 500s.
- **`person_email` is the most sensitive field** — peer-enumeration of crew emails was the original motivating bug for the `resume_published` gate. Treat any change that loosens its null-masking with extra care.
- **`EventCrewPoolMember.role: str = "main"`** in this same file is intentionally still a bare string — that's a request payload, not a response, and the input validation strategy hasn't been migrated to the enum yet. Don't "fix" it without checking the open question on input-side enum coverage.

## Cross-cutting concerns

- **`rule::event_crew::status_enum`** — this schema is the named `enforces` claim for that rule. The rule documents the canonical 6 states + transitions; the schema enforces the *value* half (not transitions) at response time. Change to the canonical enum must update both the model enum class and this schema's typed fields together.
- **`rule::crew_visibility::peer_pii_resume_gated`** — the four `person_*` PII fields plus the `resume_published` flag exist *for this rule*. The schema accepts nulls so the rule's enforcement (in `services/visibility.py` + `_event_crew_to_read`) has a place to land. The companion endpoint `/crew/visible` on `boats.py` implements the same rule with row-omission semantics instead of null-masking — divergence noted in the rule's open questions.
- **Auth**: every endpoint returning this schema runs `_get_user_sailing_event_or_404` + `_require_can_view_sailing_event` first. The schema itself is auth-agnostic; viewer identity reaches it only through the `include_pii` flag decided upstream.
- **Websocket / calendar**: status changes that flow through these endpoints also bump `ics_sequence` and emit `event_crew.updated` (see EventCrew model dossier). The schema doesn't surface `ics_sequence` — that field is internal.

## External consumers

- **Concorda web (`concorda-web`)**: `EventCrewMember` interface at `~/concorda-web/src/lib/api.ts:1695` is a hand-mirrored TypeScript copy of this schema. The TS file already defines `EventCrewStatus` / `EventCrewRole` literal unions at lines 1683–1693 with a comment pointing back to the Python enum as source of truth. Any field added/renamed/typed here needs a matching edit there.
- **Concorda iOS app (Expo)**: consumes the same crew endpoints. New status values or schema field changes need a coordinated mobile release.
- **None of the schema fields are persisted by external systems** (no webhook, no scheduled export currently uses this shape).

## Open questions

- **Should `EventCrewPoolMember.role` and `EventCrewMarkResponse.action` move to enum types too?** They're request-side schemas in this same file using bare `str` with comments enumerating valid values — the same drift `dd72f2f` just fixed for responses. Pending.
- **Does Pydantic v2 serialize `EventCrewStatus` members as the underlying string by default?** The `(str, Enum)` mixin means JSON output is the string value, but if a future Pydantic upgrade changes that behavior, every API client breaks silently. Worth a contract test.
- **PII gate consistency**: `_event_crew_to_read` null-masks; `boats.py::list_visible_crew` row-omits. Both serve `rule::crew_visibility::peer_pii_resume_gated`. Should this schema grow a `visibility_hidden: bool` flag so frontends can show "hidden crew member" placeholders, or is null-masking the final answer? Deferred per the rule's open questions.
