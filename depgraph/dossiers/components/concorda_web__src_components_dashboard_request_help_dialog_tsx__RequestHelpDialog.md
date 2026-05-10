---
node_id: concorda-web::src/components/dashboard/request-help-dialog.tsx::RequestHelpDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 756de1d1a478ddc5a13a97181147cf49e2f3917a5fd16aa250d3ca8337573ae5
status: current
---

# RequestHelpDialog

## Purpose

Provides a modal interface for users to send support messages to the MBSA team. It wraps a standard `Dialog` component and uses the `supportApi` to transmit the message. It is designed to be used as a wrapper (via `children`) or as a standalone button within the dashboard.

## Invariants

- **Requires `useAuth` context** to retrieve the current user's email for the success state display.
- **Calls `supportApi.requestHelp(message: string)`** to transmit the data.
- **Trims whitespace** from the input message before submission to prevent sending empty-space-only messages.
- **Returns a success state** that displays the user's email to confirm where the reply will be sent.

## Gotchas

- **State reset timing:** A 200ms `setTimeout` is required in the `useEffect` cleanup to reset the `message`, `error`, `sent`, and `submitting` states. This prevents the form from flickering back into view or showing old data when the user re-opens the dialog after a successful submission (per commit `05bc09b`).
- **Empty message guard:** The `handleSubmit` function returns early if the trimmed message is empty, preventing unnecessary API calls.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to access the current user's identity.
- **Audit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.
