---
node_id: GET::/api/boats/{0}/detail
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d551a47ba4c780ae70f3d1fde7608e460af6ad7eca2a8d0837d3a272eeed9268
status: llm_drafted
---

# GET /api/boats/{boat_id}/detail

## Purpose

Fetches core metadata for a specific boat, including its name, manufacturer, and physical dimensions. This endpoint is distinct from `get_boat_resume`, which provides more extensive technical specifications. An agent should use this endpoint for general UI displays (like boat headers or lists) where only basic identity and physical attributes are required.

## Invariants

- **Requires `require_auth`** — The user must be authenticated via the `current_user` dependency.
- **Access is restricted by membership status** — Returns a `403 Forbidden` if the user is not part of the crew or if their membership status is not `"active"` or `"invited"`.
- **Returns a fixed JSON shape** — Includes `id`, `sail_number`, `name`, `manufacturer`, `boat_class`, `length`, `picture_url`, and `banner_url`.
- **Uses `getattr` for optional fields** — Fields like `manufacturer` and `length` are retrieved using `getattr` to prevent `AttributeError` if the columns are missing or null on the model.

## Gotchas

- **Strict membership check** — Per commit `36ef425`, the endpoint enforces a tighter authorization check. Users with a status other than `"active"` or `"invited"` (such as those who have been removed or declined) are explicitly blocked from viewing boat details to prevent data leakage after access revocation.
- **Dependency on `_get_boat_or_404`** — If the `boat_id` does not exist, the function raises a 404 via the internal helper before checking membership.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and validates membership via `_get_crew_membership`.
- **Side effects**: Changes to boat identity or crew status (e.g., via `boat_coowner_removal` seen in the same file) will immediately affect the ability to call this endpoint.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.getDetail`
