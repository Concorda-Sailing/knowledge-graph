---
node_id: concorda-web::src/components/admin/club-dialog.tsx::ClubDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e422f32acacfe39bcb749a4119a6ff3e04a6f07e71ddb1f2f2a6d2a5b73004a0
status: llm_drafted
---

# ClubDialog

## Purpose

The `ClubDialog` is a modal component used for creating or editing organization-level details. It handles the state for both new organization creation and the editing of existing ones (via `clubId`). It is distinct from the `DeleteConfirmDialog` in that it manages complex form state and data fetching for organization metadata, rather than just a confirmation action.

## Invariants

- **`clubId` determines mode** — If `clubId` is present, the component enters "edit mode," fetching existing data from `organizationsApi.get(clubId)`.
- **`onSuccess` is the primary completion signal** — The component must call `onSuccess` after a successful create or update to trigger UI refreshes in the parent view.
- **`vhf_channel` must be cast to string** — The API may return a numeric value, but the form state requires a string to avoid type mismatches during `setFormData`.
- **`open` prop controls data fetching** — The `useEffect` hooks for fetching members and regions are gated by the `open` prop to prevent unnecessary API calls when the dialog is closed.

## Gotchas

- **Mobile layout constraints** — Per commit `0564f06`, admin dialogs must cap width and stack the footer on `<md` breakpoints to prevent broken layouts on mobile devices.
- **Region selection dependency** — Per commit `11a19fa`, the `region` field is now a specific selector in this dialog, requiring the `constantsApi.getAll()` call to populate the list.

## Cross-cutting concerns

- **Auth**: Uses `adminApi` and `organizationsApi` which require authenticated admin sessions.
- **Side effects**: Triggers a refresh of the `AdminListPage` via the `onSuccess` callback.

## External consumers

None known.
