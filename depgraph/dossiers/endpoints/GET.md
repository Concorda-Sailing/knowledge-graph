---
node_id: GET::/
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d1c3cdb2a1faab7dae7f6997a5e77e692977febc26d2463afd31f03dd6f44c67
status: llm_drafted
---

# GET /

## Purpose

The root endpoint provides a basic connectivity and versioning check for the Concorda API. It serves as a heartbeat to confirm the service is reachable and to communicate the current API version to clients.

## Invariants

- **Returns a JSON object** containing the keys `message` and `version`.
- **Method is strictly GET.**
- **Version is currently hardcoded to `"1.0.0"`**.

## Gotchas

- **CORS and Origin sensitivity:** Per commit `0158f8c`, the API is sensitive to allowed origins; while this endpoint is public, it is part of the service that relies on the local network IP/CORS configuration to allow web-client access.
- **Static file pathing:** The root-level configuration is adjacent to the `/api/uploads/photos` mount. Per commit `283e149`, the system relies on specific directory structures (`/opt/concorda/{database,photos,documents}`) for media serving; ensure any changes to the root or static mounts do not break the path resolution for these assets.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
