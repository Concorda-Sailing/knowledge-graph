---
node_id: concorda-web::src/lib/api.ts::organizationsApi.exportCsv
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c7cba2136acc12d63789dd4b8814feaf85a185aa3b67e823347c00e2288cf817
status: llm_drafted
---

# organizationsApi.exportCsv

## Purpose

Triggers a server-side generation of a CSV file containing organization data. This method is used to provide administrators with a downloadable snapshot of their organization's records. It is distinct from `importCsv`, which handles the reverse flow of uploading a file to update the organization state.

## Invariants

- **Returns a `Blob` object.** The method returns the raw binary stream from the fetch response, which must be handled as a blob in the UI to allow for browser-based downloads.
- **Uses `GET` method.** The underlying request is a simple GET to the `/api/organizations/export/csv` endpoint.
- **Requires Bearer Authentication.** Unlike the standard `fetchApiAuthenticated` wrapper used in the rest of the `organizationsApi`, this manually constructs the headers using `getAuthToken()`.

## Gotchas

- **Manual header construction.** Because this uses a raw `fetch` rather than the `fetchApiAuthenticated` helper, it must manually check for the existence of the token and attach the `Authorization` header. If the `getAuthToken()` logic changes, this method may fail to authenticate.
- **Error handling is opaque.** If the export fails, the method throws a generic `Error("Export failed")` without attempting to parse the response body for details, unlike the `importCsv` method which attempts to extract a `detail` string from the JSON response.

## Cross-cutting concerns

- **Auth**: Uses `getAuthToken()` to inject a Bearer token into the request headers.
- **Side effects**: Used by `AdminClubsPage` to allow administrators to export their organization's data.

## External consumers

- `concorda-web::src/app/members/admin/clubs/page.tsx` (via `AdminClubsPage`)
