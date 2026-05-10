---
node_id: concorda-web::src/lib/api.ts::approvalsApi.vote
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5dbc153c1dc29d3098373c6c85dc6efcf406b568f9fd871da6edda820ee4e12b
status: current
---

# approvalsApi.vote

## Purpose

Client-side mirror for casting a vote on a pending approval request (boat co-owner invite, co-owner promotion, co-owner removal, ownership transfer — registered in `concorda-api/services/approval_types/`). The approvals system is a generic N-of-M sign-off engine that gates state transitions whose authorization can't be expressed as a single role check: any voter can `rejected` to kill the request, and `approved` only resolves the request once the per-type rule (`unanimous`, `majority`, or `first_responder`) is satisfied. This thin wrapper just POSTs `{decision, reason?}` to `/api/approval-requests/{id}/vote` and trusts the backend to tally, finalize, and fire the type-specific `on_approve`/`on_reject` side effects (e.g. activating a co-owner BoatCrew row). A future Claude touching this should treat the call as fire-and-forget for state — re-fetch the request (or invalidate the inbox/list query) to see the resolved status.

## Invariants

- `decision` is exactly `"approved"` or `"rejected"`. The backend rejects anything else with 400; do not pass `"pending"` or `"canceled"`.
- `reason` is optional and only meaningful on `rejected` — backend stores it as `resolution_reason` on the request when the rejection is what finalizes the vote.
- The endpoint returns the *full updated* `ApprovalRequest` (with embedded `votes[]`); callers should prefer the response over a separate refetch when updating local state.
- Only seeded voters can call this. Caller must already be a voter row on the request — backend returns 403 otherwise. Don't show the vote UI to non-voters.
- A voter cannot vote twice (409 "You have already voted"); UI must disable buttons once `vote.decision !== "pending"` for the current user.

## Gotchas

- **Co-owner invite acceptance has a hidden membership precondition**: see `47688ac feat(coowner): require Boat Owner membership to accept co-owner invite`. If the invitee approves a `boat_coowner_invite` without an active Boat-Owner-granting product, the backend returns 400 with copy that points to "My Profile → Membership". Surface that error verbatim — it's instructional, not just an error.
- The `/api/invite/respond` dispatcher (`88d8f1c feat(invite): wire response page to unified dispatcher endpoint`) is a *separate* path from this one. Email Accept/Decline links go through `inviteResponseApi.respond`, which internally maps `accepted`/`declined` to this vote call. Don't double-wire a UI to both.
- Race: if a peer rejects between when the UI loaded and when the user clicks, this returns 409 "Request already rejected". Treat 409 as "refresh and re-render" rather than a hard error toast.
- `decision: "approved"` does not mean the *request* is approved — only this voter's slot. Counting `req.votes.filter(v => v.decision === "approved").length` against `req.votes.length` only tells you the unanimous-rule progress; for `majority` or `first_responder` types the request can finalize before all slots are filled. Read the returned `req.status` rather than recomputing.

## Cross-cutting concerns

- **Auth**: `fetchApiAuthenticated` — session cookie required.
- **Side effects on finalize** (server-side, fired by `_finalize` → `spec["on_approve"]`/`on_reject`): activates/cancels the underlying `BoatCrew` row for invite/promotion/removal types, swaps the `owner` BoatCrew for ownership transfers. None of this happens client-side.
- **Notifications**: `_dispatch_notifications` sends transactional emails to the requester and remaining voters on each transition; failures are swallowed and logged, never block the vote.
- **Audit**: every vote writes `decided_at` and `reason` on the `ApprovalVote` row; resolution reason on the request is the *latest* rejection's reason.
- **No realtime push**: other voters' UIs won't update until they refetch. Inbox refresh on focus is the current story.

## External consumers

None known. The endpoint is members-only and not part of any documented external API; the iOS Expo app is the only other surface that could consume it, and as of this writing it does not.

## Open questions

- Should the 400 "Boat Owner membership required" be returned as a structured error code rather than a freeform string? Consumers currently regex/contains-match the copy.
- No expiry-on-vote interaction is encoded here — `sweep_expired` is its own scheduled path, but there's no client signal that a request is *about* to expire. Worth a TTL hint in the response payload?
