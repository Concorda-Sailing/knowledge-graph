---
node_id: concorda-web::src/components/inbox/outgoing-row.tsx::OutgoingApprovalRow
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ad71b1aadd7a754125a01351ac8646c7d3e692de95ca9bd0a92a9dee8c794653
status: current
---

# OutgoingApprovalRow

## Purpose

Renders a single row in the user's inbox representing an outgoing approval request (e.g., a boat co-owner request). It provides a summary of the request type, the expiration date, and a "Cancel request" action. Use this component when a user needs to manage or revoke requests they have initiated, rather than responding to incoming ones.

## Invariants

- **Requires an `ApprovalRequest` object** via the `req` prop to access `id`, `expires_at`, and `request_type`.
- **Calls `approvalsApi.cancel(req.id)`** to execute the cancellation logic.
- **Uses `formatInOrgTz` for expiration display** to ensure the expiration time is rendered in the organization's timezone rather than the user's local time.
- **Disables the button during the async `cancel` operation** via the `busy` state to prevent duplicate API calls.

## Gotchas

- **Timezone-sensitive rendering:** Per commit `f444b4c`, all backend datetimes (specifically `req.expires_at`) must be rendered using the organization's timezone via `formatInOrgTz`. Failing to do so will display the wrong expiration time to users in different timezones.
- **Dependency on `approvalsApi`:** The component relies on the `approvalsApi.cancel` method; if the API contract for cancellation changes, this component will fail to execute the primary user action.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to call `approvalsApi.cancel`.
- **Side effects**: Triggers the `onChanged` callback, which typically causes the `InboxList` to re-fetch or refresh the list of active requests.

## External consumers

None known.
