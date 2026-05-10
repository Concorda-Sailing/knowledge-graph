---
node_id: concorda-web::src/lib/api.ts::mediaApi.listFiles
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f73a3affacfccd8bb89bda1ab9df6d12ee591bdea33d7761264fe0880a8d0629
status: llm_drafted
---

# mediaApi.listFiles

## Purpose
Client-side mirror for listing media files — the folder-browse / filter primitive behind every UI surface that shows uploaded documents or photos. Issues an auth-gated `GET /api/media/files` with optional `folder_uuid`, `entity_type`, `entity_uuid`, `document_type`, and `owner_uuid` filters and resolves to `MediaFile[]`. Three components consume it: the admin file manager (`admin/files/page.tsx`, no filters — see-everything view), the boat documents tab (`boat-documents.tsx`, filtered by `entity_type=boat` + `entity_uuid` then post-filtered to drop `document_type=photo`), and the boat photos tab (`boat-photos.tsx`, same entity filter plus `document_type=photo`). A future Claude editing this should treat it as a thin transport: filter parameters compose AND-style server-side, and visibility is decided by the backend's scope/owner gate — the client must not pre-filter for permission.

## Invariants
- Path is `/api/media/files` (plural, no trailing slash); query params are URL-encoded via `URLSearchParams` and only appended when truthy — empty strings must not produce `?folder_uuid=`.
- All five filters are optional and combine with logical AND server-side; passing none returns the full set the caller is allowed to see.
- Response is `MediaFile[]`, sorted by `created` descending; callers relying on order must not assume ascending.
- Auth is mandatory (`fetchApiAuthenticated`); unauthenticated calls throw rather than returning `[]`.
- Server-side scope filter (non-admin): caller sees a row iff `scope in {public, crew}` OR `owner_uuid == self` OR `uploaded_by_uuid == self`. `private` files owned by others are invisible. Admins (`system_admin` / `org_admin`) bypass.
- `owner_uuid` filter is gated: non-admins passing `owner_uuid != self` get 403 — not an empty list. This is a deliberate enumeration block.

## Gotchas
- The `owner_uuid` 403 gate exists because without it any authenticated user could iterate person UUIDs and harvest filenames/sizes/hashes of every public+crew file. Don't "soften" the 403 to an empty array — that re-opens the enumeration hole. Same gate exists on `listFolders`.
- `boat-documents.tsx` filters out `document_type === "photo"` *client-side* after fetching. If you add a `document_type__ne` server param, migrate that caller; otherwise photos will leak into the documents tab on any code path that bypasses the post-filter.
- Admin page calls `mediaApi.listFiles()` with **no filters** — for a system_admin this returns every file in the org including other members' `private` scope. That's intentional (moderation), but means previewing this page as a non-admin via role-impersonation will look broken.
- Filters are exact-match only — no `LIKE`, no `entity_uuid IN (...)`. The admin page's `search` and scope/type dropdowns filter the result array in JS, not via the API.
- The sibling `serve_file` endpoint had a DB-session-lifetime incident on 2026-05-06; `list_files` doesn't stream, but anything added here that fans out per-row (thumbnail URLs, signed links) must not hold the session across IO.

## Cross-cutting concerns
- Auth: bearer token via `fetchApiAuthenticated`; server enforces `require_auth` + scope filter + admin bypass + `owner_uuid` enumeration gate.
- Side effects: none (read-only).
- No websocket — peers won't see new uploads or deletions until they refetch. `boat-documents` and `boat-photos` re-fetch after their own mutations; no cross-tab/cross-client coherence.
- No rate limit specific to this route (general API limiter applies; see `auth.py` single-worker constraint memo).
- Result includes `file_path` / `mime_type` / `size_bytes` / hash — treat the response as a leak surface if scope rules are ever loosened. The enumeration gate is the only thing standing between a curious member and other members' file metadata.
- No pagination — full result set is returned. The admin page will degrade if the org accumulates thousands of files.

## External consumers
None known. Web-only — Expo iOS app does not currently browse media. No scheduled jobs, webhooks, or third-party integrations hit this route.

## Open questions
- Should `boat-documents` get a server-side `document_type__ne=photo` (or an inverse filter) instead of post-filtering, so the contract is honored without trusting the caller?
- Should non-admin `owner_uuid != self` return 200-empty instead of 403, to avoid signaling "this UUID exists"? Trade-off vs. the current explicit-deny posture.
- Should the admin page paginate or window the result set before file count becomes a real perf problem?
- Should boat-scoped docs/photos be visible to boat owners/co-owners regardless of `scope`, separate from the global `public/crew/self` rule? Today a co-owner only sees `private` boat docs if they uploaded them.
