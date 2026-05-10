---
node_id: concorda-web::src/lib/api.ts::norApi.uploadAndExtract
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a4bbb5c13ade4241621297cf20a644291f026a9a3f7a39803a4b566258342e37
status: llm_drafted
---

# norApi.uploadAndExtract

## Purpose
`norApi.uploadAndExtract` is a specialized service for uploading a file and triggering an immediate extraction process via the NOR (Notice of Readiness) pipeline. It is distinct from `norApi.extract`, which only triggers extraction on an existing `fileId`. A future agent should reach for this function when the user is providing a new file (via a `File` object) and requires the extracted data (like `extracted_data` or `extracted_items`) to be returned in the same request cycle.

## Invariants
* HTTP Method: `POST`.
* Endpoint: `/api/nor/upload-and-extract`.
* Authentication: Requires a valid Bearer token; throws an explicit "Not authenticated" error if `getAuthToken()` is empty.
* Payload: Uses `multipart/form-data` containing a `file` and a `document_type`.
* Return Shape: Returns a `Promise<NORExtractResponse>` containing optional `extracted_data` (Record) and `extracted_items` (Array of Records).

## Gotchas
* **Manual Error Handling**: Unlike `fetchApiAuthenticated`, this function uses a raw `fetch` call and manually parses the error response to extract the `detail` field from the JSON body (lines 3238-3240).
* **Default Type**: The `documentType` defaults to `"nor"` if not explicitly provided.
* **Silent JSON Failures**: The error detail extraction contains a `try/catch` block that suppresses errors if the response body is not valid JSON, which might hide the true cause of a failed request.

## Cross-cutting concerns
* **Auth**: Requires manual token retrieval via `getAuthToken()` and explicit header injection.
* **Side Effects**: Triggers backend extraction logic which may involve heavy processing/LLM calls on the server.

## External consumers
* `concorda-web::src/app/members/admin/events/import-social/page.tsx` (ImportContent)
* `concorda-web::src/app/members/admin/events/import/page.tsx` (ImportRacesContent)

## Open questions
* None.
