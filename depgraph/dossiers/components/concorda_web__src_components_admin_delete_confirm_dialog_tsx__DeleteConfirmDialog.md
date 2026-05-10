---
node_id: concorda-web::src/components/admin/delete-confirm-dialog.tsx::DeleteConfirmDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f3c2d3e172822f013e9aab91effcaead13b0c376a74df4a2688fb23e1187ab16
status: current
---

# DeleteConfirmDialog

## Purpose

A specialized UI component for presenting a high-stakes confirmation dialog before a destructive action is executed. It wraps the `AlertDialog` pattern to provide a consistent visual warning (e.g., red "destructive" buttons) and context-specific messaging (e.g., "Delete race?") to prevent accidental data loss. Use this instead of a generic `AlertDialog` when an admin action requires a confirmation step that should visually signal danger to the user.

## Invariants

- **`onConfirm` must be a function.** The component relies on this callback to execute the actual deletion logic after the user clicks the action button.
- **`itemType` is required.** This string is injected directly into the title (`Delete {itemType}?`) to provide context for the deletion.
- **`destructive` prop controls button styling.** When `true`, the action button uses the `bg-destructive` class to signal a high-risk operation.
- **`itemName` is optional.** If provided, the description includes the specific name of the item in quotes; otherwise, it falls back to a generic warning.

## Gotchas

- **Commit `b6ca664` introduced this as part of the admin-list-page feature.** It is a new component and currently lacks a specialized "loading" state for the confirm button, meaning the UI might appear unresponsive if the `onConfirm` action takes time to resolve.

## Cross-cutting concerns

- **Auth**: None. This is a UI-only component; the actual permission check must happen in the parent component or the API layer.
- **Side effects**: Triggers the deletion of admin-managed entities (e.g., races, series, or users) via the `onConfirm` callback.

## External consumers

None known.
