---
node_id: concorda-web::src/hooks/use-pending-approvals.ts::usePendingApprovals
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 042548df9f79e1cce5f4bac84ce371cc13e07414a6f341e2ca24f1223cb6f005
status: current
---

# usePendingApprovals

## Purpose

React hook fronting a module-scoped singleton cache of the current user's pending approval requests. On mount (or after `STALE_MS` since last fetch), it double-fires `approvalsApi.list({requester: "me"})` and `approvalsApi.list({voter: "me"})` in parallel, dedupes the two result sets by id (an item where you are both requester and voter is treated as outgoing only), and exposes `incoming`/`outgoing`/`urgent`/`refresh`/`isLoading`. `urgent` is derived per-render as incoming items whose `expires_at` falls inside a 48h window. Three consumers share the singleton: the sidebar inbox badge, the dashboard urgent banner, and the inbox list page — so a single fetch fans out to all three, and one component calling `refresh()` (currently only `InboxList`) updates them all.

## Invariants

- Cache, `inflight`, `pending`, and the listener set are module-level singletons — there is exactly one store per browser tab. Do not move them inside the hook.
- `incoming` and `outgoing` must be disjoint by `id`. The dedupe (outgoing wins) lives in `fetchNow`; replacing the two-call shape with a single endpoint must preserve this.
- `useSyncExternalStore` must receive stable function references for `subscribe`/`getSnapshot` — keep them module-scope, not inlined.
- `getServerSnapshot` must return an SSR-safe, deterministic empty cache (no `Date.now()`, no fetch).
- `urgent` is derived from `snap.incoming` only — outgoing items never count as urgent for the current user, even if they are about to expire.
- Failures on either underlying `approvalsApi.list` call degrade to `[]` via `.catch(() => [])`; the hook never throws and never surfaces an error state. If a real error UI is added, change both call sites together.

## Gotchas

- Only one commit in history (`8b87dd3 feat(inbox): add usePendingApprovals hook`); no battle-scars yet — assume gotchas are latent.
- Coalescing logic: while a fetch is `inflight`, additional `fetchNow()` calls set `pending = true` and re-fire exactly once on settle. Calling `refresh()` rapidly will not stack N fetches, but it also will not return a promise tied to your specific call — callers awaiting `refresh()` get the in-flight promise, not a fresh one.
- `STALE_MS = 30s` gating lives in the mount effect with an empty dep array, so navigating between the three consumer surfaces inside 30s reuses the cached snapshot silently. There is no visibility/focus refetch and no websocket invalidation — a vote cast in another tab will not update this tab until something explicitly calls `refresh()` or 30s elapses on next mount.
- `URGENT_WINDOW_MS` is computed against `Date.now()` at render time, not memoized — `urgent` is recomputed on every render of every consumer. Cheap today (small arrays) but do not push expensive derivation into this filter.
- Dedupe uses `req` (requester=me) as the outgoing set and filters it out of `vote` (voter=me). If the API ever returns the same request to both endpoints with different field shapes, the outgoing copy wins — incoming-shape fields would be silently dropped.

## Cross-cutting concerns

- Auth: both underlying calls are `fetchApiAuthenticated`; an expired session yields `[]` (caught), so a logged-out user sees empty inbox/badge/banner rather than an error.
- Sidebar badge math: `InboxNavItem` adds `incoming.length + outgoing.length` to `useInboxCrewRequests` counts — changing the dedupe direction (e.g. making self-approvals appear in both) would double-count the badge.
- `InboxList.refreshAll` chains `refresh()` with `useInboxCrewRequests.refresh()` after a vote; both must complete for the list to reconcile. The hook's `refresh` does not return a promise the caller can await — if sequencing ever matters, return `fetchNow()`'s promise instead of wrapping it.
- No audit/telemetry side effects; pure read path.

## External consumers

None known. Internal-only; no mobile/Expo consumer yet, no server component reads this (it is `"use client"` and SSR snapshot is intentionally empty).

## Open questions

- Should this subscribe to a websocket event (`approval.created`/`approval.voted`) instead of relying on 30s staleness + explicit `refresh()`? The dashboard urgent banner in particular goes stale silently.
- `refresh` returning `void` while internally returning a promise is a small API lie — worth tightening if any caller ever needs to know "the refetch I just triggered is done."
