---
node_id: concorda-api::schemas/boat.py::PunchlistItemRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7b235d337bb67211c94318bc2f6f5ab0a54ce7a698825f47702a8e78574edd1f
status: llm_drafted
---

# PunchlistItemRead

## Purpose

Pydantic response schema for a single boat-punchlist item (the boat's maintenance/repair todo list: "replace windex," "wax hull," etc). Serializes a `BoatPunchlistItem` row plus two server-resolved person joins (`created_by_name`, `assigned_to_name`) into the wire shape the web client consumes as `PunchlistItem`. It is the response model for three router endpoints — `GET /api/boats/{id}/punchlist` (returns a list), `POST /api/boats/{id}/punchlist`, and `PUT /api/boats/{id}/punchlist/{item_id}`. Editing this schema is editing the contract for the entire boat-punchlist surface; the web counterpart `boatApi.getPunchlist` and its three siblings type-cast against the resulting JSON, and there is no separate detail endpoint.

## Invariants

- `importance` and `status` are typed `str` on the wire, not enums. UIs treat them as `high|medium|low` and `open|in_progress|done` respectively, but the schema enforces neither — see Open questions.
- `created_by_uuid` is required (NOT NULL) because the router sets it from `current_user.id` at create time; `assigned_to_uuid` is optional.
- `created_by_name` / `assigned_to_name` are populated by the router helper `_punchlist_to_read` (boats.py:100) via a `Person` join — they are NOT SQLAlchemy relationships and Pydantic's `from_attributes` alone will not fill them. Any new endpoint returning this schema must go through `_punchlist_to_read` or a functional equivalent.
- `from_attributes = True` (Pydantic v2): callers may pass either a dict (as the helper does today) or an ORM instance. Don't break the dict path — all three current callsites use it.
- `created` / `modified` are `datetime` and serialize as naive-UTC per the project-wide `UtcDateTime` convention (see memory `feedback_naive_datetime_convention`).

## Gotchas

- The join-name fields silently drop to `None` if the referenced `Person` is missing (deleted user, orphaned `assigned_to_uuid` after a crew removal). The UI shows blank rather than an error — a stale assignment is invisible. No backfill or constraint guards this today.
- Field order in `PunchlistItemRead` does not match `PunchlistItemUpdate` (Update lacks `created_by_uuid`, `boat_uuid`, timestamps, and the join fields). If you add a field to Read, decide explicitly whether Update should accept it — they have drifted before and the router's `model_dump(exclude_unset=True)` will happily mass-assign anything on the Update model.
- Recent commit history on `schemas/boat.py` is sparse (last touch `68a7508`, migrations 048–056). The punchlist schema specifically has not been battle-tested by a recent fix/revert cycle — treat edge cases as unverified.
- The schema's `description` and join-name fields default to `None`; if you change `description` to required, every existing row with NULL description will fail validation on read.

## Cross-cutting concerns

- **Auth:** all three consuming endpoints require `_require_crew_or_owner` (any active `BoatCrew` row); delete is gated separately to creator-or-owner but doesn't return this schema.
- **Websocket:** mutating endpoints (POST/PUT/DELETE) broadcast `PUNCHLIST_UPDATED` keyed on `boat_id` after commit. The Read schema is the payload-of-record for what consumers re-fetch; keeping field stability matters for cache reconciliation.
- **Audit:** none. Punchlist mutations are not captured by the audit/approvals system, so the schema's `created`/`modified` are the only forensic trail.
- **PII surface:** `created_by_name` and `assigned_to_name` expose first+last name of crew members to any active crew reader. This is consistent with `BoatCrewRead` peer visibility for active crew, but be aware if punchlist visibility ever broadens beyond active crew.

## External consumers

None known. No Expo/iOS surface for punchlist today (iOS app focuses on schedule/crew). No webhooks, scheduled jobs, public API, or third-party integrations consume this schema.

## Open questions

- Should `importance` and `status` become Pydantic `Literal` (or DB CHECK) enums? Free strings mean a typo writes through and the UI silently mis-buckets it.
- Should the schema expose a `created_by_picture_url` / `assigned_to_picture_url` to match `BoatCrewRead`'s richer person join? Today's UI shows initials only.
- Is `assigned_to_uuid` referentially validated against the boat's current crew, or can it point at any Person? The schema accepts any string; the router does not check membership.
