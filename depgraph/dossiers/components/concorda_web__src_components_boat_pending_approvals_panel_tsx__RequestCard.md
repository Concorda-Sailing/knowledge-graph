---
node_id: concorda-web::src/components/boat/pending-approvals-panel.tsx::RequestCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1bd087297be35e1c9e87f6d8ad46d579502e8719f8f4a5c86d3c50b5700e0a05
status: llm_drafted
---

# RequestCard

## Purpose

Renders an individual approval request within the pending approvals panel. It provides the UI for an owner to either accept or reject a request, including an optional text input for a rejection reason. This is a leaf component used by the `pending-approvals-panel` to allow granular interaction with specific `ApprovalRequest` objects.

## Invariants

- **Requires an `ApprovalRequest` object** containing a `votes` array to calculate progress.
- **The `onChanged` callback must be called** after both `accept` and `reject` actions to trigger a refresh of the parent list.
- **The `reason` state is local to the card**; if the user types a reason but doesn't click "Reject" immediately, the state is lost if the component unmounts.
- **`reject` can send an empty string or `undefined`** for the reason, as the API handles the optionality of the rejection text.

## Gotchas

- **`reason` input is not cleared on accept**: If a user types a reason and then clicks "Accept", the `reason` state persists in the component's memory until the component is unmounted or the parent triggers a full re-render of the list.

## Cross-cutting concerns

- **Auth**: Relies on `approvalsApi.vote`, which requires an authenticated session with owner/admin permissions.
- **Side effects**: Triggers `onChanged` which, in the context of the `pending-approvals-panel`, refreshes the list of pending requests for the boat owner.

## External consumers

None known.
