---
node_id: concorda-test::lib/api-client.ts::ApiClient.listApprovalRequests
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 149af649a33a622c12dfcbbac37729e9fe29834d3997e847653de0dbd6b44543
status: llm_drafted
---

# ApiClient.listApprovalRequests

## Purpose

Test-harness wrapper around `GET /api/approval-requests` — the same listing endpoint the prod web client's `approvalsApi.list` fronts (see `concorda_web__src_lib_api_ts__approvalsApi_list.md` for the underlying contract). Used by 7 Playwright specs across `tests/boats/coowner-*.spec.ts`, `tests/api/approvals.spec.ts`, and `tests/auth/email-link-flows.spec.ts` to drive co-owner invite/accept/reject flows: the requester (Bob) reads `requester=me` to find the request he just created and assert status; the voter (Carol/Dan) reads `voter=me` to find the inbox row before calling `voteOnApprovalRequest`; and `subject_uuid=` is used to fetch the post-resolution row by id when the spec needs the full vote history. It exists because Playwright specs need to assert on approval state without scraping the UI — the wrapper is the only sanctioned path.

## Invariants

- Exactly one of `voter`, `requester`, `subject_uuid` should be supplied per call. The TS signature makes all four params optional, but the underlying API returns 400 if none are provided. Calls in this repo always supply exactly one of the three discriminators (sometimes plus `status`).
- `voter` and `requester` are typed `'me'` literal — only-self enumeration. Cross-user inspection in tests goes via `subject_uuid` (which the requester always knows because they captured `request.id`/`request.subject_uuid` at create time).
- Result is unordered. Server returns `q.all()` with no `order_by`. Specs that care about a specific row filter by `id` / `request_type` / `subject_uuid` rather than indexing `[0]`.
- `ApprovalRequest` returned here is the test-client interface (line 559) — it does **not** model the enriched `boat_uuid` / `boat_name` / `requester_name` fields the API actually returns. `coowner-inbox.spec.ts:54` reads `boat_uuid` through a cast; if you add new specs filtering on enrichment, cast or extend the interface.

## Gotchas

- **Privacy filtering on `subject_uuid` is silent.** Non-admin callers only see rows where they're the requester or a seeded voter; the Python router filters post-fetch. So `bob.listApprovalRequests({ subject_uuid: X })` and `carol.listApprovalRequests({ subject_uuid: X })` legitimately return different lengths for the same X. `coowner-approval-vote.spec.ts:46` works around this by having Carol (requester) look up the subject_uuid first and pass it to Bob (voter).
- **No status validation server-side.** An unknown `status` returns `[]`, not 400. A typo'd status filter looks like "no pending approvals" — same shape as the empty-success case. If a spec starts mysteriously seeing zero rows after a refactor, check the status string.
- **No retry / no waitFor.** Approvals are created synchronously by `createApprovalRequest`, so the listing is consistent immediately on the same DB connection. But specs that race `voteOnApprovalRequest` on one client against `listApprovalRequests` on another may see the pre-vote `status: 'pending'` if they don't `await` the vote first. All current call sites await, but this is easy to break.
- **`cancelStalePendingInvitesForBoat`** in `coowner-inbox.spec.ts:46-59` is the canonical "clean up before re-running" pattern — copies it if you write new co-owner specs that need idempotent setup against a non-wiped DB.

## Cross-cutting concerns

- **Auth**: Bearer token via `setToken` / `login`. Each spec creates per-persona `ApiClient` instances (`bob`, `carol`, `dan`, `alice`) — the `voter=me` / `requester=me` semantics depend entirely on which client's token is set. Don't share a client across personas.
- **TLS**: Module-level `NODE_TLS_REJECT_UNAUTHORIZED = '0'` (line 9) — fine for the test host's self-signed cert, would be a vuln in any other context.
- **Side effects**: Pure read. No audit rows, no notifications, no DB writes.
- **DB wipe**: Specs assume the test host has been wiped + reseeded between runs (see `feedback_no_local_test_runs.md`). Stale approval rows from a prior run will leak into `requester=me` results otherwise.

## External consumers

None. Test-harness only — not consumed by the prod web app, the Expo iOS app, or any external integration. The prod equivalent is `approvalsApi.list` in `concorda-web/src/lib/api.ts`.

## Open questions

- Worth widening the `ApprovalRequest` interface (line 559) to include the enriched `boat_uuid` / `boat_name` / `requester_name` fields so the cast at `coowner-inbox.spec.ts:54` goes away? Currently three specs cast through `unknown`.
- The wrapper accepts a `status` filter but no spec exercises the multi-status case. If a future "show approved + rejected" inbox view ships, this signature may need to accept `status: string | string[]`.
