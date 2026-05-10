---
node_id: concorda-test::lib/api-client.ts::ApiClient.rawRequest
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e27e850ad05fbaf5bd0ce637d51f82c7bd8fbfe13f70b7d2043ce07fe3bf74f3
status: current
---

# ApiClient.rawRequest

## Purpose

Provides a low-level escape hatch for making arbitrary HTTP requests to the API. It is used primarily for "negative-path" testing where the agent needs to verify how the system handles unauthorized, forbidden, or malformed requests (e.g., 400/401/403 status codes). Unlike the high-level methods like `post` or `get`, this method allows explicit control over the `method`, `path`, and `token` to simulate various authentication and request states.

## Invariants

- **Method and Path are required.** The caller must provide a valid HTTP verb and a relative path starting from the base URL.
- **Optional `token` override.** If a `token` is passed, it overrides the instance's `this.token`; if `undefined`, it defaults to the instance's current bearer token.
- **Returns a raw `Response` object.** Unlike other methods in this class that return parsed JSON, this returns the unparsed `Response` to allow tests to inspect status codes and headers directly.
- **JSON Body serialization.** If a `body` is provided, it is automatically stringified via `JSON.stringify`.

## Gotchas

- **Manual Header Management.** While it sets `Content-Type: application/json` by default, it does not support complex multi-part or custom header-heavy requests without modifying this method.
- **Auth bypass risk.** Because it accepts an explicit `token` argument, tests can easily simulate "wrong user" scenarios by passing a token from a different `ApiClient` instance.

## Cross-cutting concerns

- **Auth**: Uses the instance's `this.token` unless a specific `token` is passed in the arguments.
- **Rate limit**: None (standard `fetch` behavior).
- **Side effects**: Used in `approvals.spec.ts` and `cross-context-crew.spec.ts` to validate error states for approval and crew operations.

## External consumers

None known.
