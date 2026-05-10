---
node_id: concorda-web::src/lib/api.ts::checkApiHealth
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 939dc764845c3d9ae902e4a4589552b1ab1f75e6c576d9f9455db0df095b62e1
status: llm_drafted
---

# checkApiHealth

## Purpose

Performs a lightweight connectivity check by hitting the `/health` endpoint. It is used to verify that the backend is reachable and responsive before the application attempts to initialize complex state or authenticated flows.

## Invariants

- **Returns a boolean.** Returns `true` if the response status is in the `ok` range (200-299), otherwise `false`.
- **Uses a 5-second timeout.** The `AbortSignal.timeout(5000)` ensures the check does not hang the application initialization if the network is black-holed.
- **Relies on `API_BASE_URL`.** The request path is relative to the base URL defined in the module.

## Gotchas

- **Dependency on `API_BASE_URL` logic.** If the environment is not configured correctly, `API_BASE_URL` might be an empty string, causing the fetch to hit the local origin instead of the intended API.
- **Admin visibility.** Per commit `6fe57db`, the health status is used to drive the "Health response-times table" in the admin drawer; changes to this function's response shape or timing can impact admin monitoring visibility.

## Cross-cutting concerns

- **Auth**: None (uses a public health endpoint).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by the `AuthProvider` (via `auth-context.tsx:102` and `119`) to determine readiness/connectivity state.

## External consumers

None known.
