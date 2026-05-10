---
node_id: POST::/api/regattas
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a686917568719d6169866164777b54c5ef1d43dc021e7d575d985044a4b01a32
status: current
---

# POST /api/regattas

## Purpose

Creates a new regatta record in the database. This endpoint is the primary way to initialize a regatta, handling the generation of a unique slug from the provided name and managing the association with Organizing Authorities (OAs). It is distinct from `update_regatta` in that it handles the initial `set_regatta_oas` assignment and the creation of the base `Regatta` entity.

## Invariants

- **HTTP Method is POST** to `/api/regattas`.
- **Requires `_require_manager` authentication** via the `current_user` dependency.
- **Must pass `_require_oa_scope`** if `organizing_authority_uuids` are provided in the payload.
- **Returns a `RegattaRead` model** which includes attached counts via `_attach_counts`.
- **Generates a unique slug** automatically using `_generate_slug` and `_ensure_unique_slug`.

## Gotchas

- **Multi-OA scope enforcement**: Per commit `058aa8c`, the endpoint must strictly enforce that the user has permission to assign the provided `organizing_authority_uuids`. A user cannot create a regatta and assign it to an OA they do not represent.
- **Slug regeneration on name change**: While this is a POST endpoint, the logic for `_ensure_unique_slug` is shared with the PUT method; ensure that any logic changes to slug generation are reflected in both to prevent collisions during the initial creation.
- **Count attachment**: The return shape is not just the raw database row, but a model with counts attached via `_attach_counts`. If the count logic changes, this endpoint's response shape changes.

## Cross-cutting concerns

- **Auth**: Requires `_require_manager` and validates scope via `_require_oa_scope` for the provided `oa_uuids`.
- **Side effects**: Triggers the creation of the regatta entity which is a prerequisite for all subsequent regatta-related features (schedules, matches, etc.).

## External consumers

- `concorda-web` (via `regattaApi.create`)

## Open questions

- Should the slug generation be more configurable (e.g., allowing custom slugs) or remain strictly derived from the name to maintain consistency with the `update_regatta` re-slugging logic?
