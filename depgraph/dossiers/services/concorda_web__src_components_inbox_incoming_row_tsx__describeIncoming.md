---
node_id: concorda-web::src/components/inbox/incoming-row.tsx::describeIncoming
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bf24b26b593055468f68ca37c1db2e836c212ce2788ddf2a080c5758fb1571aa
status: llm_drafted
---

# describeIncoming

## Purpose

Generates the human-readable string used to describe an incoming approval request (e.g., co-owner invites or removals). It transforms the raw `request_type` and `boat_name` into a natural language sentence for the inbox UI. This is a pure utility function used by the `IncomingApprovalRow` component to ensure the user understands exactly what action is being requested before they interact with the `approve` or `reject` buttons.

## Invariants

- **Input is an `ApprovalRequest` object.** It relies on `r.request_type` to determine the sentence structure.
- **Fallback for `boat_name`.** If `r.boat_name` is null or undefined, it defaults to the string `"your boat"`.
- **Fallback for `requester_name`.** If `r.requester_name` is missing, the "from [name]" suffix is omitted entirely.
- **Returns a string.** The output is used directly in a `<span>` within the `AlertDescription`.

## Gotchas

- **Timezone rendering dependency.** Per commit `f444b4c`, any datetime display logic (like the expiration date in the parent component) must use the organization's timezone rather than the browser's local time to avoid displaying incorrect expiration windows to users.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A (The parent component `IncomingApprovalRow` triggers the `approvalsApi.vote` which handles the audit/write side).
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
