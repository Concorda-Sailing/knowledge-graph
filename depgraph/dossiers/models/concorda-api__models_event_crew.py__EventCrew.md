---
node_id: concorda-api::models/event_crew.py::EventCrew
node_kind: model
feature: events-crew
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3674c17ff29195977e738428655ba6c3cfbb3c31a474e4884c3ff20d23706e5d
status: current
---

# EventCrew

## Purpose

Per-event crew assignment row. One `EventCrew` represents one
person's slot for one sailing event: pool member, invitee, accepted
crew, declined invite, confirmed crew, or self-nominated request.
Unique on `(sailing_event_uuid, person_uuid)` — one person can hold
at most one slot per event.

This is the central table for the **crew lifecycle**: pool → invited
→ accepted/declined → confirmed (or requested → accepted/declined for
self-nominations). The lifecycle has a logigraph rule
(`rule::event_crew::status_enum`) capturing the canonical 6 status
values + valid transitions. The ontology entry
(`resource::concorda::event_crew`) describes the entity in plain
language.

The model file also defines the **canonical enum classes**:
`EventCrewStatus(str, Enum)` and `EventCrewRole(str, Enum)`. These
are the source of truth for valid values; new code should reference
enum members rather than string literals.

## Invariants

- **`status` is one of `EventCrewStatus`'s 6 values**: `pool`,
  `invited`, `accepted`, `declined`, `confirmed`, `requested`. Writes
  go through enum members; reads with bare string literals still work
  because of the `(str, Enum)` mixin. See
  `rule::event_crew::status_enum` decision table for transitions.
- **`role` is one of `EventCrewRole`'s 2 values**: `main` or
  `alternate`. Drives roster evaluation; alternates auto-promote when
  a main declines.
- **Uniqueness on `(sailing_event_uuid, person_uuid)`** is enforced
  via constraint. Adding a person to an event twice fails.
- **Default status is `pool`**, default role is `main`. The
  `EventCrewStatus.POOL.value` and `EventCrewRole.MAIN.value` are
  used as the column defaults explicitly so the enum stays
  authoritative.
- **Datetime columns inherit `UtcDateTime` from BaseModel** —
  `created`, `modified` are stored naive-as-UTC.

## Gotchas

- **The `status` column is `String(20)` for backwards compatibility.**
  No CHECK constraint or SQLAlchemy Enum type — a misspelled status
  would land in the DB. The Pydantic schema (`EventCrewRead.status:
  EventCrewStatus`) catches malformed values on response, but
  malformed inserts via raw SQL or imports could still corrupt.
- **`responded_by_uuid` is semantically conflated.** It's set
  whenever status moves to `accepted`/`declined`, but the value is
  *whoever made the change*: the crew member self-responding (their
  own ID), or the boat owner marking a verbal response (owner's ID),
  or the owner accepting a crew-request (owner's ID, not the
  requester's). See open question on
  `rule::crew_visibility::peer_pii_resume_gated`.
- **`invited_by_uuid` may be null** for self-nominations
  (`status=requested`) since no one invited them. Email reply-to
  logic falls back to the boat owner if invited_by is missing — see
  `routers/events.py::_resolve_skipper`.
- **Pool → accepted self-promotion**: when an owner sends invites
  (`POST crew-invite`), if the owner is in the pool their row
  auto-transitions to `accepted` instead of `invited` (no
  notification to self). See `services/crew_roster.py::notify_crew`.
- **Crew-request acceptance has a side effect**: accepting a
  `requested` row via `respond_to_crew_request` ALSO creates a
  `BoatCrew` row promoting the requester to active boat crew (so
  they're a member beyond this single event). Declining does not.
  See `routers/events.py::respond_to_crew_request` and
  `services/invite_dispatch.py::_EventCrewHandler.respond`.
- **Alternate promotion is automatic**: when a `main` crew declines,
  `services/crew_roster.py::evaluate_roster` promotes the next
  `alternate` (priority order) to `main` and transitions their
  status to `invited` if it was `pool`.

## Cross-cutting concerns

- **Auth**: writes are gated by relational checks (boat owner /
  crew member self) on the routers. PII fields on response are
  gated by `rule::crew_visibility::peer_pii_resume_gated`.
- **Email/notification**: state transitions trigger emails via
  `services/crew_roster.py::_send_crew_notification` and
  `utils/notification_utils.py::notify_person`. The
  `confirm_event_crew` endpoint hardened on 2026-05-10 to handle
  send failures gracefully (state commits before notifications
  attempt; per-recipient try/except).
- **Websocket**: state changes broadcast `event_crew.updated` so
  clients refetch.
- **`ics_sequence`** is incremented on certain state changes to
  invalidate Apple/Google calendar caches when the .ics is
  regenerated.

## External consumers

- **Concorda iOS app** consumes the crew list endpoints; new status
  values (if ever added) need coordinated app release.
- **Calendar feed** (.ics) reflects EventCrew status indirectly via
  SailingEvent counts.

## Open questions

- **When does the column type tighten?** Moving `status` to
  `SQLAlchemy Enum` type or adding a CHECK constraint requires a
  migration; pending.
- **Should `responded_by_uuid` be split** into `responder_uuid`
  (the crew member whose decision this is) and
  `response_recorded_by_uuid` (whoever physically made the change)?
  Surfaces in audit-trail questions. Pending decision.
- **Should there be a `state machine` rule** capturing the legal
  status transitions (so an illegal transition fails at the call
  site, not just the DB)? Currently the type system only validates
  values, not transitions. See open question on
  `rule::event_crew::status_enum`.
