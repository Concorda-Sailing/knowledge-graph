---
node_id: POST::/api/nor/upload-and-extract
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eb6909035960357df3c7066d43701f514a2cf572356dc5ac2e1692cf07240b74
status: llm_drafted
---

# POST /api/nor/upload-and-extract

## Purpose

A convenience endpoint for uploading a document and immediately triggering the NOR (Notice of Race) extraction pipeline. It handles the file storage via the media system and then invokes `extract_nor` to parse the uploaded content. Use this when a user is submitting a document that requires immediate processing rather than a two-step upload-then-process flow.

## Invariants

- **HTTP Method:** `POST`
- **Auth:** Requires a valid user session via `require_auth`.
- **File Size Limit:** Maximum 20MB.
- **Input Types:** Must include a `file` (Multipart/Form-data) and a `document_type` string.
- **Return Shape:** Returns a `NORExtractResponse` containing `extracted_data`, `extracted_items`, and a `file_id`.

## Gotchas

- **MIME Type Strictness:** Per commit `8c74a42`, the endpoint must preserve `vision` MIME types to ensure extraction metadata is not lost during the handoff to the LLM pipeline.
- **Storage Pathing:** Files are stored in a user-specific directory (`/media/{user_id}/{uuid}{ext}`). Ensure the `current_user.id` is used to prevent cross-user directory collisions.
- **Extraction Dependency:** This is a synchronous wrapper around `extract_nor`. If the extraction service is slow or fails, this endpoint will hang or return an error, potentially blocking the client-side UI.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to ensure the `current_user` is authenticated and has a valid session.
- **Audit**: Writes a `MediaFile` record to the database, establishing ownership and a permanent record of the upload.
- **Side effects**: Triggers the LLM-based extraction pipeline via `extract_nor`.

## External consumers

- `concorda-web::src/lib/api.ts::norApi.uploadAndExtract`
