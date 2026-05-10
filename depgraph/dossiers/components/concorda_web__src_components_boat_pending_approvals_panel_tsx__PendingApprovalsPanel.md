---
node_id: concorda-web::src/components/boat/pending-approvals-panel.tsx::PendingApprovalsPanel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 17691910b59012e2bd2f33d6c1c120c2974ddb8126b59d937b506fe89f908c64
status: llm_drafted
---

# PendingApprovalsPanel

## Purpose

Displays a list of pending approval requests for the current user (the "owner" or "voter"). It provides a high-level summary of the request type and progress, allowing the user to either approve or reject a request with an optional text reason. This component is intended for the boat-owner view to facilitate quick decision-making on pending changes.

## Invariants

- **Fetches via `approvalsApi.list`** using the specific filter `{ voter: "me", status: "pending" }`.
- **Returns `null` if no requests are pending**, preventing an empty card from rendering in the UI.
- **The `RequestCard` sub-component manages its own local `reason` state** for the rejection flow.
- **Calls `onChanged` (the parent's `refresh` function) after every vote** to ensure the list stays in sync with the server state.

## Gotchas

- **The `reason` state is only utilized during the `reject` action.** If a user types a reason and clicks "Accept", the reason is ignored by the API call in `accept()`.
- **The `reject` function uses `reason || undefined`** to ensure the payload matches the expected `ApprovalRequest` signature when no text is provided.

## Cross-cutting concerns

- **Auth**: Relies on `approvalsApi` which requires a valid session/token to resolve the `"me"` identity.
- **Side effects**: Successful votes trigger a refresh of the local list; if this is used in a dashboard, it ensures the "pending" count remains accurate.

## External consumers

None known.
