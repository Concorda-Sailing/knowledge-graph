---
node_id: concorda-web::src/lib/api.ts::norApi.uploadAndExtract
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a4bbb5c13ade4241621297cf20a644291f026a9a3f7a39803a4b566258342e37
status: current
---

# norApi.uploadAndExtract

## Purpose

Handles the multipart/form-data upload of a file to the NOR (Notice of Race) extraction service. It wraps a `POST` request to `/api/nor/upload-and-extract` that accepts a `File` and a `document_type`. Use this when a user is uploading a document that needs to be parsed into structured data (e.g., `extracted_data` or `extracted_items`).

## Invariants

- **Method is `POST`** — The endpoint expects a multipart form-data body.
- **Requires authentication** — Calls `getAuthToken()` and injects it into the `Authorization` header; throws an error if no token is present.
- **Default `document_type` is `"nor"`** — If no second argument is provided, the API assumes a Notice of Race document.
- **Returns `Promise<NORExtractResponse>`** — The response is parsed as JSON and includes fields like `file_id`, `file_url`, and extracted data objects.
- **Error handling is explicit** — If `res.ok` is false, the function attempts to parse the JSON body to extract a `detail` string for the error message.

## Gotchas

- **Manual `FormData` construction** — Unlike `fetchApiAuthenticated` used in sibling methods, this uses a raw `fetch` call to ensure the `FormData` boundary and `file` attachment are handled correctly for the multipart upload.
- **Error detail extraction** — If the server returns a non-JSON error body, the `try/catch` block in the `.then` chain prevents a crash by defaulting the error message to the status code (e.g., `"400"`).

## Cross-cutting concerns

- **Auth**: Requires a valid bearer token via `getAuthToken()`.
- **Side effects**: Successful extraction is used by the import flows in `ImportContent` and `ImportRacesContent` to populate structured data from uploaded files.

## External consumers

- `concorda-web::src/app/members/admin/events/import-social/page.tsx`
- `concorda-web::src/app/members/admin/events/import/page.tsx`
