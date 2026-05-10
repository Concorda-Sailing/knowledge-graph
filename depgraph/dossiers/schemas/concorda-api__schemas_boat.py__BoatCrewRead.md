---
node_id: concorda-api::schemas/boat.py::BoatCrewRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2f39f5602107a759029d9a2867de33230fafd8d3554e1d0de3ec574a99a203d9
status: current
---

# BoatCrewRead

## Purpose

The wire-format Pydantic schema for `BoatCrew` rows returned by the boat-crew API surface. It mirrors the `BoatCrew` model's columns (`role`, `status`, `position`, `priority`, `invited_by_uuid`, `notes`) and adds four denormalized `person_*` fields (`first_name`, `last_name`, `picture_url`, `email`) that the route handlers join in so the crew tab and crewfinder UIs don't have to follow up with N person lookups. `from_attributes = True` means routers can pass an ORM row directly when the join columns are aliased onto it; otherwise the handler builds the dict by hand. Used by the five `/api/boats/{id}/crew*` endpoints — read, add, invite, reorder, update.

## Invariants

- **Field set is a strict superset of `BoatCrew` columns plus the four `person_*` joins.** Anything else (resume snippets, last-sail dates, crewpool membership) belongs in a different schema — keep this one cheap so the crew list stays fast.
- **`status` and `role` are free-form `str`.** The model defends them as String(20) with `.lower()` checks; if you tighten this to a Literal/enum here, you must tighten the model in lockstep or you'll start rejecting legacy rows that exist in prod.
- **`priority: int = 0` default matches the model.** The owner-pick ordering convention (per `project_invite_priority_order`) is "first click = 1"; 0 means "unranked / legacy." Don't change the default to 1 — existing rows would silently jump rank.
- **`person_email` is exposed.** This is intentional for owners/managers viewing their own crew, but the route handler is responsible for stripping it when a non-owner peer is the caller (per `feedback_crew_visibility_privacy`). The schema itself does not enforce privacy.

## Gotchas

- **The five dependent endpoints don't all return the same shape in practice.** `POST /crew/invite` returns a row where `status="invited"` and `person_email` may be the only populated person field (invitee hasn't joined yet); `GET /crew` returns fully-joined rows. Callers must handle missing `person_first_name` even though it's `Optional`.
- **`invited_by_uuid` is a raw uuid string, not a joined object.** There's no `invited_by_name` field — the UI looks the inviter up separately or skips showing it. If you add that join, add it here too; don't let the route handler smuggle an extra key past the schema.
- **`config_uuid` is not validated against the boat.** The model dossier flags this — no FK enforces same-boat. The schema won't catch a mismatched config either; it's the route's job.
- **`from_attributes = True` + joined columns is fragile.** If you rename a join alias in the route SQL (e.g. `person_first_name` → `first_name`) without updating this schema, Pydantic silently returns `None` for the field. Recent crew-roster refactor (commit `68a7508`) touched both sides; verify both move together.

## Cross-cutting concerns

- **Auth:** All five consuming endpoints require the caller to be a member of the boat or org admin; this schema carries no auth metadata of its own.
- **Privacy filter:** Per memory `feedback_crew_visibility_privacy`, peer crew identities are hidden unless the published resume opts in. Filter happens in the route before serialization — the schema returns whatever the route hands it.
- **Websocket:** Mutating endpoints broadcast `boat_crew.updated`; the payload is typically a `BoatCrewRead` dump, so adding a heavy field here bloats every websocket frame.
- **iOS app:** Renaming any field is a breaking change for old client builds (see model dossier's external-consumers note).

## External consumers

- **Concorda iOS app** decodes this shape on every crew screen.
- **concorda-web** `boatApi.getCrew` and the crew picker bind to these field names.
- **concorda-test** fixtures and Playwright specs assert on `role`, `status`, `priority`, and the `person_*` joins.

## Open questions

- Should `status` and `role` become `Literal` types here, with a single source of truth shared with the model? Today they drift via convention only.
- `invited_by_name` would save a round-trip on the crew tab — worth adding, or does it belong in a heavier `BoatCrewDetail` variant?
