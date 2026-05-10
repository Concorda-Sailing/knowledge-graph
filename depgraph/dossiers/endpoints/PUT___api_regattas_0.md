---
node_id: PUT::/api/regattas/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4b3cd39eacaa0211ed3079343031c612302ae1a02da04154fd5672daef8a5a84
status: llm_drafted
---

# PUT /api/regattas/{regatta_id}

## Purpose

Updates the properties of an existing regatta. This endpoint is the primary way to modify regatta metadata, including its name and its associated Organizing Authorities (OAs). It is distinct from the creation flow as it handles the complex logic of re-slugging the URL and re-assigning organizational scope.

## Invariants

- **Method is `PUT`** and requires a valid `regatta_id`.
- **Requires `_require_manager` authentication** via the `current_user` dependency.
- **Enforces organizational scope** via `_require_regatta_org_scope` to ensure the user has permission to modify this specific regatta.
- **Returns a `RegattaRead` model** which includes computed counts via `_attach_counts`.
- **Updates the `slug` automatically** if the `name` field is changed in the request body.

## Gotchas

- **Multi-OA Reassignment Security**: Per commit `fdc87b4`, changing the `organizing_authority_uuids` is not just a data update; it is gated by `_require_oa_scope`. This prevents a user from "moving" a regatta to an organization they do not represent.
- **Slug Collisions**: The `_ensure_unique_slug` call (line 221) means that if a name change results in a duplicate slug, the system will append a suffix. This is a side effect of the `name` change logic.
- **Partial Updates**: The endpoint uses `exclude_unset=True` on the model dump. This means if a field is omitted from the JSON body, the existing value in the database remains unchanged.

## Cross-cutting concerns

- **Auth**: Uses `_require_manager` for identity and `_require_regatta_org_scope` for resource-level authorization.
- **Side effects**: Modifying a regatta name triggers a slug regeneration, which may affect any external systems or hardcoded links relying on the previous URL structure.

## External consumers

- `concorda-web::src/lib/api.ts::regattaApi.update`

## Open questions

- The `_attach_counts` call is used at the end of the update; if the count calculation logic becomes heavy, this could impact the latency of the `PUT` request.
