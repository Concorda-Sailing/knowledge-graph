---
node_id: concorda-api::schemas/regatta.py::RegattaRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4bdc96f48ecfa05edac70a7ad0d1ee126befe3ce8b1128852820529603366511
status: llm_drafted
---

# RegattaRead

## Purpose
Backend Pydantic read schema for `Regatta` — the response shape returned by every regatta endpoint (`list`, `get-by-id`, `get-by-slug`, `create`, `update`). Fields cover identity (`id`, `slug`, `type`), timing (`start`, `end`, `first_warning`), descriptive metadata (`name`, `description`, `location`, `image_url`, `start_area_text`, `start_area_location`), classification (`region_uuid`, `course_type`, `qualifier`, `classes`, `scoring_system`), competitive config (`max_races`, `rc_channel`), free-form `links`/`additional_events`, plus two computed/joined extras: `match_counts` (populated by `_attach_counts` for list/get) and `organizing_authorities` (denormalized OA summaries from the join table). A future Claude editing this should remember it is the *contract* shared by five route handlers and consumed by `regattaApi.list/get/getBySlug/create/update` on the web — adding a field here implicitly promises every endpoint will populate it.

## Invariants
- `from_attributes = True` — instances are built directly from `Regatta` ORM rows via `RegattaRead.model_validate(r, from_attributes=True)`. Every non-Optional field must exist on the model OR be assigned before validate.
- `match_counts` is `Optional` because it is *not* an ORM column — `_attach_counts` writes it onto the row in-process before validate. List/get endpoints populate it; create/update do not (the create response will have `match_counts=None`).
- `organizing_authorities: list[OrganizingAuthoritySummary] = []` is also synthesized from the `OrganizationRegatta` join — it is not a `relationship()` on the model. Empty list is the correct "no OAs" answer, not `None`.
- Mirrors the `Regatta` SQLAlchemy model field-for-field for the persisted columns. If you add a column, add it here AND to `RegattaCreate`/`RegattaUpdate` or the round-trip breaks.
- `id`, `type`, `created`, `modified`, `name` are the only required fields; everything else is nullable to support partially-populated drafts.

## Gotchas
- There is no regatta-level `accepting_crew` / `accept_crew_requests` field, and don't reintroduce one. `b67d359` and `6c9b5f3` deliberately moved that toggle to per-`SailingEvent` (see `RosterBoat.accept_crew_requests` in this same module). The web's "Accepting Crew" badge reads from match-roster / per-race toggles, not from this schema.
- `match_counts` was added in `e1c7e44` (Regatta match counts — backend). It is computed and grafted on, not loaded — endpoints that forget to call `_attach_counts` will return `match_counts=None` and silently break list-card badges. The `delete` dossier's "list refetches after delete" pattern relies on this being populated.
- `organizing_authority_uuids` exists on `RegattaCreate`/`RegattaUpdate` (write side) but the read shape exposes the **resolved** `organizing_authorities: list[OrganizingAuthoritySummary]` instead — asymmetric on purpose. Don't "fix" this by adding `organizing_authority_uuids` to read; consumers want the names/ids together.
- `slug` is `Optional` because legacy regattas predate slugging. New writes always populate it, but read code must `.slug ?? id` for routing.
- `series_uuid` / `region_uuid` / `oa_uuid` are loose `String(36)` references with no FK enforcement (see the `delete` dossier) — a `RegattaRead` row can carry a uuid pointing at a deleted parent. Consumers that resolve these must tolerate misses.
- `classes`, `qualifier`, `scoring_system`, `additional_events`, `links` are typed as bare `Optional[list]` / `Optional[dict]` — no inner schema. The web treats them as opaque JSON; tightening the types is a breaking change for every consumer that currently shrugs at the shape.

## Cross-cutting concerns
- **Auth/visibility**: the schema itself imposes nothing, but every endpoint that returns it is gated by `require_auth` and Tier C cross-org scoping (`058aa8c`). A leaked `RegattaRead` from a private org would be an upstream bug, not a schema concern.
- **Coupling to `_attach_counts`**: list, get-by-id, and get-by-slug all share one count-attaching helper. Divergence between list and detail badges implies the helper, not the schema.
- **Web mirror**: `concorda-web/src/lib/api.ts` defines `RegattaDetail` as the TS twin. Field additions here that the web doesn't mirror are silently dropped by `fetchApiAuthenticated<RegattaDetail>` — coordinate the two.
- **No audit, no websocket** — pure read shape; serialization has no side effects.

## External consumers
None known directly — the schema is internal to the API. Indirectly consumed by the web app's `regattaApi.*` family and by the `concorda-test` Playwright harness via `ApiClient.listRegattas` / `getRegatta`. No Expo, no webhooks, no scheduled jobs deserialize this shape today.

## Open questions
- Should `classes`, `scoring_system`, `qualifier`, `additional_events`, `links` get typed inner schemas? Today's "opaque JSON" stance is convenient but means the contract carries no validation — drift between writers and readers is invisible until a UI renders garbage.
- Should `match_counts` be split into a separate `RegattaListRow` vs. `RegattaDetail` shape, given that create/update legitimately return `None`? The current "Optional, sometimes populated" idiom hides the endpoint-by-endpoint contract.
