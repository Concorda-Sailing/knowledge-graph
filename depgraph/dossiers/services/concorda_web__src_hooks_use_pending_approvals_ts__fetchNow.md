---
node_id: concorda-web::src/hooks/use-pending-approvals.ts::fetchNow
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 23595b3055501c0a287ef82d725a76a3b515b6c8d3b60226af57f415bf6d06de
status: llm_drafted
---

# fetchNow

## Purpose

The `fetchNow` function is the core engine for refreshing the pending approvals state. It performs two concurrent API calls to `approvalsApi.list`—one for requests sent by the user (`requester: "me"`) and one for requests received by the user (`voter: "me"`)—and merges them into a single cache object. It is distinct from the `usePendingApprovals` hook, which is the consumer-facing React interface; `fetchNow` handles the low-level orchestration, concurrency control, and state-syncing logic.

## Invariants

- **Uses `Promise.all` for concurrency** — It fetches both incoming and outgoing lists simultaneously to minimize total latency.
- **Implements a single-flight pattern** — The `inflight` variable ensures that multiple simultaneous calls to `fetchNow` do not trigger redundant network requests.
- **Returns a `Promise<void>`** — The function returns the `inflight` promise, allowing callers to await completion, though the actual state update happens via the internal `cache` mutation.
- **Filters incoming requests against outgoing IDs** — To prevent a request from appearing in both the `incoming` and `outgoing` lists, it uses `outIds` to filter the `vote` results.

## Gotchas

- **Recursive retry on completion** — If a fetch is triggered while another is already `pending`, the `finally` block calls `fetchNow()` again. This ensures that if a user triggers a refresh during an active fetch, the new request is queued rather than dropped.
- **Silent failure on API error** — The `.catch(() => [])` on both `approvalsApi.list` calls ensures that a single failed endpoint doesn't break the entire refresh cycle, but it also means a failed fetch results in an empty list rather than an error state.

## Cross-cutting concerns

- **Auth**: Relies on the `approvalsApi` instance, which requires a valid session/token to resolve the `"me"` alias.
- **Side effects**: Triggers a re-render of any component using `usePendingApprovals`, specifically affecting the "urgent" filter logic and the inbox view.

## External consumers

None known.
