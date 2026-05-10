---
node_id: GET::/api/media/folders
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 55961a096a95040176f95fdfcf6352cd4a1e6aa768d538b17c213376e0de9fb2
status: current
---

# GET /api/media/folders

## Purpose

Retrieves a list of media folders based on hierarchical and ownership constraints. It allows for filtering by `parent_uuid`, `owner_uuid`, and `owner_type` to facilitate tree traversal and scoped views. Unlike the `POST` or `PUT` endpoints in this module, this is a read-only operation designed to support both administrative oversight and user-specific private views.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns a list of `FolderRead` objects** ordered by `sort_order` and then `name`.
- **Admin override capability**: Users with `system_admin` or `org_admin` roles can bypass the `owner_uuid` restriction to view any folder.
- **Scope-based filtering**: Non-admins are restricted to seeing only folders where the scope is `public`, `crew`, or where they are the explicit `owner_uuid`.

## Gotchas

- **IDOR protection is strict**: Per commit `c9a7c41` (security: tier-A IDOR audit fixes), the endpoint enforces that a non-admin cannot query a folder by an `owner_uuid` that does not match their own.
- **Strict ownership for creation**: While this is the GET endpoint, the sibling `POST /folders` endpoint (see `3fa5fef`) enforces that only admins can set an `owner_uuid` different from the `current_user.id`.
- **Ordering dependency**: The result set is explicitly ordered by `sort_order`. If a client-side UI expects a different sort (e.g., alphabetical only), it must account for this server-side preference.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` and checks for `system_admin` or `org_admin` roles for elevated visibility.
- **Rate limit**: None explicitly defined for this GET endpoint, but media-related endpoints are subject to the general media-service rate-limiting patterns.
- **Side effects**: Changes to folder structure or ownership (via `POST` or `PUT`) will immediately change the visibility of folders in this list for non-admin users.

## External consumers

None known.
