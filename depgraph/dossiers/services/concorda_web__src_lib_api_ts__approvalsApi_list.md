---
node_id: concorda-web::src/lib/api.ts::approvalsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b6ce2aaa92160c800b3374dd7aa538df534ca61fee9a69c576a8bde247869f1b
status: llm_drafted
---

# approvalsApi.list

## Purpose

Client-side mirror for the `GET /api/approval-requests` collection endpoint — the only way to enumerate approval requests, fronting three mutually-exclusive query modes: `voter=me` (the inbox / "things waiting on me"), `requester=me` (outbox / "things I started"), and `subject_uuid=<uuid>` (history for a specific subject row, e.g. a boat-crew transition). It exists because there is no single "list all my approvals" endpoint — the backend deliberately splits voter/requester/subject lookups so the privacy scoping can differ per axis. Three call sites consume it: `PendingApprovalsPanel` (boat owner page, voter=me), and the singleton store in `hooks/use-pending-approvals.ts` which fires *both* requester+voter variants in parallel and dedupes by id to feed the inbox list, the dashboard urgent banner, and the sidebar nav badge.

## Invariants

- Exactly one of `voter`, `requester`, `subject_uuid` must be supplied — supplying none returns 400 `"Provide voter=me, requester=me, or subject_uuid"`. The TS type makes them all optional, but the runtime contract is "exactly one." Don't assume an empty-args call returns "everything."
- `voter` and `requester` only accept the literal string `"me"`. The router does string equality against `"me"` — any other value silently falls through to the 400 branch.
- `status` is a freeform string filter and only meaningful on the `voter`/`requester` branches. The `subject_uuid` branch ignores `status` entirely (router does not pass it through to `list_requests_for_subject`).
- Returned shape is `ApprovalRequest[]` with embedded `votes[]`, plus `boat_uuid`/`boat_name`/`requester_name` enrichment when resolvable. Treat enrichment fields as optional — they only appear when the join hits.
- Known `status` values: `"pending"`, `"approved"`, `"rejected"`, `"expired"`, `"canceled"`. There is no validation server-side; an unknown status returns `[]` (silent empty), not an error.

## Gotchas

- **No server-side ordering.** `list_requests_for_voter` / `_for_requester` / `_for_subject` all return `q.all()` with no `order_by`. Result order is whatever the SQLite query planner emits — do not rely on newest-first or any stable ordering. Sort client-side by `created_at` if you need it.
- **`subject_uuid` is privacy-scoped, not open.** Non-admins only see rows where they are the requester or a seeded voter; the router filters in Python after fetching. Admins (`system_admin` / `org_admin`) bypass. So the same `subject_uuid` query returns different lengths for different callers — don't cache by `subject_uuid` alone.
- **The hook double-fires and dedupes.** `use-pending-approvals.ts` calls `list({requester:"me", status:"pending"})` and `list({voter:"me", status:"pending"})` in parallel and removes voter-rows whose id is already in the requester set (the `outIds` filter at line 39–42). Self-approval requests would otherwise appear in both buckets. If you add a fourth caller mode here, mind that dedupe.
- **Errors swallowed in the hook.** Both list calls have `.catch(() => [])` — a transient API failure produces an empty inbox with no toast. The inbox UI shows "no pending approvals" indistinguishably from the error state. Don't add behavior that *depends* on error visibility from this layer; surface errors at the call site if needed.
- **`PendingApprovalsPanel` bypasses the singleton store.** It calls `approvalsApi.list` directly with its own local state, so its data is independent of the inbox cache. Voting in the panel triggers its `onChanged` refetch but does *not* invalidate the hook's cache — sidebar badge counts can lag until the hook's next focus refresh.

## Cross-cutting concerns

- **Auth**: `fetchApiAuthenticated` — session cookie required; 401 from the underlying fetch helper redirects to login.
- **No realtime**: list is poll-only. The hook re-fetches when `Date.now() - lastFetched > 30_000ms` on mount; there's no websocket invalidation. After `approvalsApi.vote` / `cancel`, callers must manually call `refresh` to update the inbox.
- **Audit / side effects**: pure read; no writes, no notifications, no audit rows.
- **N+1 potential**: `_to_read` runs per-row in the router, doing 1–3 extra queries (votes, optional BoatCrew→Boat, requester Person). For a large pending-set this is unbounded; today the realistic ceiling is dozens per user, but a future "all org approvals" admin view would need batching.

## External consumers

None known. Members-only endpoint; not part of any documented public API. The Expo iOS app does not currently consume it.

## Open questions

- Should ordering be made deterministic server-side (e.g. `ORDER BY created_at DESC`)? Three independent consumers each sorting client-side is duplicated effort and a source of subtle UI diffs.
- Should the `voter`/`requester` params accept a person UUID for admins, or stay locked to `"me"`? Currently any cross-user inspection has to go through `subject_uuid` plus admin role.
- Worth adding a combined endpoint (`?inbox=me`) that returns deduped requester+voter in one round trip, replacing the parallel-fetch dance in `use-pending-approvals.ts`?
