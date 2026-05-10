---
node_id: GET::/api/media/serve/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d49031cdc1f46aa4ee379f9ad9c958df53612ae867d153aa256a775358b5d63d
status: current
---

# GET /api/media/serve/{filename}

## Purpose

Serves media files (images, documents, etc.) from the local filesystem to the client. It provides a specialized streaming endpoint that resolves authentication manually to avoid the common pitfall of holding database connections open during long-running file transfers. Use this endpoint when you need to serve files that require scope-based access control (public, crew, or private) via either a Bearer token in the header or a `token` query parameter.

## Invariants

- **Manual Session Management**: The `SessionLocal` is opened and closed within the function body to ensure the connection returns to the pool before `FileResponse` begins streaming.
- **Path Traversal Protection**: The `filename` is used to look up a `MediaFile` record via an exact `file_url` match, and the resulting `disk_path` is validated against the `DOCUMENTS_DIR` root.
- **Dual-Mode Auth**: Accepts authentication via the `Authorization: Bearer <token>` header or a `token` query parameter (primarily for `<img>` tag compatibility).
- **Strict Scope Check**: If the file is not `public`, the request must provide a valid token that resolves to a user with appropriate permissions via `_can_access_file`.

## Gotchas

- **Connection Pool Exhaustion**: Do not use standard `Depends(get_db)` or `get_current_user` dependencies here. Per **Incident 2026-05-06**, using standard dependency injection causes the database session to remain open during the entire duration of the file stream, which leads to `QueuePool TimeoutError` when multiple clients download large files.
- **ORM Attribute Access**: All required attributes from the `MediaFile` object (e.g., `file_path`, `file_type`) must be extracted into local variables before the `finally: db.close()` block executes. Accessing ORM-managed attributes after the session is closed will trigger a `DetachedInstanceError`.
- **Path Validation**: The `disk_path` must be explicitly checked against `uploads_root` using `.startswith()` to prevent directory traversal attacks.

## Cross-cutting concerns

- **Auth**: Uses `get_current_user_id` to resolve identity; access is gated by `_can_access_file` based on the file's `scope`.
- **Rate limit**: None explicitly defined on this endpoint, but relies on the global API rate limiting.
- **Side effects**: N/A.

## External consumers

- Web client (for rendering images/documents in the dashboard).
- HTML `<img>` tags (via the `token` query parameter).

## Open questions

- Should we implement a more robust way to handle `token` expiration for public-facing `<img>` tags to avoid long-lived URLs in the DOM?
