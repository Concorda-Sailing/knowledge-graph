---
node_id: concorda-web::src/lib/api.ts::organizationsApi.importCsv
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4249b4e5b24f54f4546de143f5a0bb1da6358fcec9d456f80c267685b05cfb0b
status: current
---

# organizationsApi.importCsv

## Purpose

Handles the bulk upload of organization data via CSV files. It is used to transition from manual entry to batch processing for organization-level configurations. This method is distinct from the granular `orgContactsApi` methods, as it handles the multipart/form-data construction and the specific response shape required for batch import reporting.

## Invariants

- **Requires authentication.** The `getAuthToken()` must return a non-null value, or the method throws an immediate "Not authenticated" error.
- **Uses `FormData` for payload.** The file must be appended to a `FormData` object with the key `"file"`.
- **Returns a structured JSON response.** A successful import returns an object containing `{ imported: number; skipped: number; errors: string[] }`.
- **Error handling is explicit.** If the response is not `ok`, the function attempts to parse the error detail from the JSON body to provide a meaningful error message to the UI.

## Gotchas

- **Error detail extraction.** The `try/catch` block in the response handler (lines 694-695) is critical because if the server returns a non-JSON error body, a naked `res.json()` call would throw a secondary error, masking the actual HTTP status code.
- **Dependency on `getAuthToken`.** If the token retrieval logic changes or the token expires during a large upload, the method will throw "Not authenticated" before the fetch even initiates.

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token via `getAuthToken()`.
- **Side effects**: Successful imports update the organization's state, which may trigger UI refreshes in the `AdminClubsPage`.

## External consumers

- `concorda-web::src/app/members/admin/clubs/page.tsx::AdminClubsPage` (via `importCsv` call).
