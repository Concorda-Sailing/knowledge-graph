---
node_id: concorda-web::src/components/inbox/incoming-row.tsx::IncomingApprovalRow
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b67e334262236fee8eb520e6d442628d338df58b0b03008502b216b046bf62ac
status: llm_drafted
---

# IncomingApprovalRow

## Purpose

Renders a single actionable item within the user's inbox for pending approval requests (e.g., boat co-owner invites or removals). It provides the interface for a user to either "Accept" or "Reject" a request, while handling the local state for the rejection reason and the asynchronous transition states.

## Invariants

- **`accept` is a simple vote**: Calling `accept` sends a `decision: "approved"` to `approvalsApi.vote` without a reason.
- **`reject` requires a reason**: The `reject` function sends the current `reason` state (or `undefined`) to the API.
- **`upgradeRequired` logic**: If the request is a `boat_coowner_invite` and the user lacks `canManageBoats` permissions, the "Accept" button is replaced by a link to the membership subtab.
- **`onChanged` callback**: The component must call `onChanged` after a successful API call to trigger a refresh of the parent inbox list.

## Gotchas

- **Timezone rendering**: Per commit `f444b4c`, all expiration dates must be rendered using `formatInOrgTz` with the organization's timezone to avoid displaying the user's local time.
- **`reason` state is local**: The `reason` string is managed within the component; if the user types a reason but does not submit, the text is lost if the component unmounts.

## Cross-cutting concerns

- **Auth**: Relies on `canManageBoats` prop to determine if the user has the authority to act on the request.
- **Side effects**: Triggers `onChanged` which typically refreshes the inbox list view in the parent component.

## External consumers

None known.
