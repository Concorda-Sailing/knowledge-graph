---
node_id: concorda-web::src/lib/api.ts::norApi.extract
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 33f6d4654db79d12e434986bf06d1601830c095cd1ed18aa5be2031c48eb3b28
status: llm_drafted
---

# norApi.extract

## Purpose

The `norApi.extract` method triggers the extraction of data from a specific file via the backend. It is used to process uploaded documents (typically "NOR" or Notice of Race documents) to populate structured data fields. Use `extract` when you have an existing `fileId`, or `uploadAndExtract` when you need to perform the upload and extraction in a single step.

## Invariants

- **Method is `POST`** — Both `extract` and `uploadAndExtract` perform state-changing operations on the server.
- **Requires `fileId`** — The `extract` method requires a valid string identifier for a previously uploaded file.
- **Returns `NORExtractResponse`** — The response shape includes `status` ("extracted", "refused", or "error"), a `message`, and optional `extracted_data` or `extracted_items`.
- **`uploadAndExtract` uses `FormData`** — This method manually constructs a `FormData` object to handle the multipart/form-data required for file uploads.

## Gotchas

- **Manual Token Handling** — Unlike `extract` which uses the `fetchApiAuthenticated` helper, `uploadAndExtract` manually retrieves the token via `getAuthToken()` and injects it into the `Authorization` header. If the authentication logic changes, this method may bypass those updates.
- **Error Detail Extraction** — In `uploadAndExtract`, if the response is not `ok`, the code attempts to parse the JSON body to extract a `detail` field for the error message. If the server returns a non-JSON error, it falls back to the status code string.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` for `extract`, but relies on a manual `getAuthToken()` call for `uploadAndExtract`.
- **Side effects**: Successful extraction likely triggers updates to document status or metadata in the backend-driven UI components.

## External consumers

None known.
