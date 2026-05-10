---
node_id: GET::/api/media/files
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0c4b619e5dbb3e18aa443b858e329e251c00dade768de0055f3bb0b9bf8041fd
status: current
---

# GET /api/media/files

## Purpose

Retrieves a list of media files based on various filters (folder, entity, or owner). It is used to populate file browsers and asset lists within the application. Unlike the `/upload` endpoint, this is a read-only operation that implements strict visibility scoping to prevent unauthorized enumeration of user-owned files.

## Invariants

- **Returns a list of `FileRead` objects.** The response is always a JSON array of file metadata.
- **Requires authentication via `require_auth`.** Access is gated by the `current_user` identity.
- **Implements strict IDOR protection.** If a non-admin user provides an `owner_uuid`, the query must strictly match their own ID or return a 403.
- **Default ordering is descending by creation date.** Results are ordered by `MediaFile.created.desc()`.

## Gotchas

- **IDOR Vulnerability (Security Tier-A):** Per commit `c9a7c41`, the endpoint must prevent users from enumerating other users' files by passing a different `owner_uuid`. Without the `is_admin` check and the `owner_uuid != current_user.id` guard, users can harvest filenames and hashes of private files.
- **Scope-based visibility:** Non-admins are restricted by a hardcoded filter (see `or_` block in `list_files`) that limits them to `public`, `crew`, or files they personally uploaded/own.
- **Pathing dependency:** Per commit `283e149`, the underlying file storage structure assumes a specific pathing convention (`/opt/concorda/{database,photos,documents}`).

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and checks for `system_admin` or `org_admin` roles to bypass visibility filters.
- **Rate limit**: none.
- **Side effects**: none.

## External consumers

None known.
