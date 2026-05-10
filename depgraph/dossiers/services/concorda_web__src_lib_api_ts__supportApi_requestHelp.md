---
node_id: concorda-web::src/lib/api.ts::supportApi.requestHelp
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 653788645677d25726f9ce34ccaf5300a9c7c428ec688519ef9f78f3688aa2d2
status: llm_drafted
---

# supportApi.requestHelp

## Purpose

Provides a way for authenticated users to submit a support request message to the backend. It is a specialized method within `supportApi` used to transmit a text string to the `/api/support/request-help` endpoint.

## Invariants

- **Method is `POST`** — The request must use the POST verb to transmit the payload.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure the user's session/token is attached.
- **Payload shape is `{ message: string }`** — The body must be a JSON-stringified object containing exactly one `message` key.
- **Returns a success message** — The expected response shape is `{ message: string }`.

## Gotchas

- **Requires active session** — Because it uses `fetchApiAuthenticated`, this call will fail if the user is not logged in or if the token has expired.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid bearer token).
- **Side effects**: Triggers the `RequestHelpDialog` in the dashboard UI.

## External consumers

- `concorda-web::src/components/dashboard/request-help-dialog.tsx` (RequestHelpDialog)
