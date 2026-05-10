---
node_id: GET::/health
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ed4f27ccf73a68afa5c65f9f1a73106781448c8b205c6a39abbfc3019d53eed4
status: current
---

# GET /health

## Purpose

Provides a basic liveness probe for the API service. It returns a static JSON response to confirm the Python process is running and the routing engine is responsive. This is a non-authenticated endpoint used primarily for infrastructure monitoring and client-side connectivity checks.

## Invariants

- **HTTP Method**: `GET` only.
- **Path**: `/health`.
- **Response Shape**: Returns a JSON object with a single key `"status"` and value `"healthy"`.
- **No Authentication Required**: Unlike the `/api/ws` endpoint immediately following it, this endpoint does not check for a token or user identity.

## Gotchas

- **Static Response**: This is a shallow check. It only verifies that the FastAPI app is mounted and responding; it does not verify database connectivity or downstream service health.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `concorda-web::src/lib/api.ts::checkApiHealth` to verify connectivity before initiating complex client-side flows.

## External consumers

- `concorda-web` (via `checkApiHealth`)
