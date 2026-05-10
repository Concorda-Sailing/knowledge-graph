---
node_id: POST::/api/media/upload
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8f40766e6c53fed9b82262076344f3e25f7e7274c697b17918f9a78f40a8092e
status: current
---

# POST /api/media/upload

## Purpose

Handles the multipart upload of files (images, PDFs, etc.) to the server. It manages file path generation based on user ownership, performs content-type validation against a whitelist, and implements duplicate detection via SHA256 content hashing. Use this endpoint when a user needs to attach a document or image to a specific entity (e.g., a boat or a crew member).

## Invariants

- **Requires Authentication** — Uses `require_auth` to ensure a valid `current_user` is present.
- **MIME Type Validation** — Rejects uploads if the `file.content_type` is not in `ALLOWED_MIME_TYPES` or if the actual bytes do not match the declared type via `_content_matches_mime`.
- **Size Limit** — Maximum file size is strictly enforced at 50MB.
- **Ownership Constraint** — Only `system_admin` or `org_admin` can set an `owner_uuid` that differs from the `current_user.id`.
- **Returns `FileRead`** — The response model includes the `file_url` and metadata required for the frontend to display the file.

## Gotchas

- **Duplicate Detection** — If a file with the same `entity_type`, `entity_uuid`, `document_type`, and `content_hash` already exists, the API returns a `409 Conflict`.
- **Security/Magic-Byte Check** — Per commit `5f9a046`, the endpoint performs a secondary check using `_content_matches_mime` to prevent attackers from uploading malicious HTML/JS disguised as benign images.
- **DB Session Lifecycle** — Per commit `3fee226`, ensure any logic involving the response does not hold the DB session open longer than necessary to avoid streaming errors in `FileResponse`.
- **Directory Structure** — Files are stored in a nested structure: `MEDIA_DIR/{owner_uuid}/{file_uuid}{ext}`. This was restructured in commit `283e149`.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth`.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Successful uploads populate the `file_url` used by the media gallery and entity detail pages.

## External consumers

None known.
