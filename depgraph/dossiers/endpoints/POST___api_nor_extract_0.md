---
node_id: POST::/api/nor/extract/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bf1fcb9c53b4286d9983d103018b9fa8ab4c7057991a97db99be81327ede46b6
status: current
---

# POST /api/nor/extract/{file_id}

## Purpose

Triggers the LLM-based extraction of data from a previously uploaded media file (specifically for NOR or SI documents). It processes the file bytes against a specific prompt and configuration, then returns a structured response containing the extracted data or error details. This is a high-latency operation that must be handled carefully to avoid resource exhaustion.

## Invariants

- **Requires a valid `file_id`** that corresponds to an existing `MediaFile` in the database.
- **Auth is mandatory** via `require_auth`; the user must be the owner of the file, the uploader, or a `system_admin`.
- **Returns `NORExtractResponse`** which includes `status` ("extracted", "refused", or "error"), `message`, and optional `extracted_data` or `extracted_items`.
- **Mutates `MediaFile.file_metadata`** on failure to record the `extraction_error` and `extraction_status`.

## Gotchas

- **Connection pool exhaustion risk:** The DB session must be closed via `db.close()` before calling the long-running `extract_nor_from_bytes_pure`. Per commit `8b2e30a`, failing to release the session before the LLM round-trip pins a connection and causes unrelated requests to fail during parallel extractions.
- **Strict ownership check:** An `org_admin` cannot access files from other clubs unless they are a `system_admin`. Per commit `058aa8c`, this is a Tier-C security enforcement to prevent cross-org data leakage during extraction.
- **MIME type sensitivity:** The extraction process relies on preserving the correct `file_mime` and `doc_type`. Per commit `8c74a42`, the pipeline must preserve the vision MIME type to ensure the LLM processes the document correctly.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` (role-based access control).
- **Audit**: Writes to `MediaFile.file_metadata` (specifically `extraction_status` and `extraction_error`) upon failure.
- **Side effects**: Triggers a mutation on the `MediaFile` record, which is used by the UI to display extraction status.

## External consumers

- `concorda-web::src/lib/api.ts::norApi.extract`

## Open questions

- Should the extraction status be moved to a dedicated background task/worker (e.g., Celery) to completely decouple the API request lifecycle from the LLM latency?
