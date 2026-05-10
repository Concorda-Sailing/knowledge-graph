---
node_id: concorda-web::src/components/inbox/outgoing-row.tsx::describeOutgoing
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1d12b0be8d013cafe158283ae599816fb28ef8434670b54fe76b5713b538c263
status: llm_drafted
---

# describeOutgoing

## Purpose

Renders a UI row for pending approval requests initiated by the current user. It uses `describeOutgoing` to translate the `request_type` and `boat_name` into human-readable text and provides a "Cancel request" action. This is the counterpart to `IncomingApprovalRow`, used specifically for tracking requests the user has sent out (e.g., co-owner invites/promotions).

## Invariants

- **Input is an `ApprovalRequest` object.** The component relies on `req.id` for the cancellation API call and `req.request_type` for string formatting.
- **`describeOutgoing` handles three specific types:** `boat_coowner_invite`, `boat_coowner_promotion`, and `boat_coowner_removal`.
- **Expiration display is conditional.** The expiration string is only appended if `req.expires_at` is present.
- **`onChanged` must be passed from the parent.** This is called after a successful `approvalsApi.cancel` to trigger a list refresh.

## Gotchas

- **Timezone rendering must use org TZ.** Per commit `f444b4c`, all backend datetimes (like `expires_at`) must be rendered using `formatInOrgTz` with the organization's timezone rather than the browser's local time to avoid displaying incorrect expiration times to the user.
- **The `busy` state is local to this row.** While `cancel` is an async operation, the `busy` state only prevents double-clicks on this specific row instance.

## Cross-cutting concerns

- **Auth**: Uses `approvalsApi.cancel`, which requires an authenticated session.
- **Side effects**: Triggers `onChanged` (typically a list refresh in `InboxList`) upon successful cancellation.

## External consumers

None known.
