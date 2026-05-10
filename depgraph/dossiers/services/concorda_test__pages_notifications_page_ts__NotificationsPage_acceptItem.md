---
node_id: concorda-test::pages/notifications.page.ts::NotificationsPage.acceptItem
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2b776d802ea52803245c2b48784ea05bb382ce0aeab4b230764c0c808ce5fd05
status: llm_drafted
---

# NotificationsPage.acceptItem

## Purpose

Automates the acceptance of invitations within the notifications bell/dropdown. It is used to simulate a user responding to an incoming request, specifically handling the case where a "position" (role/selection) must be chosen from a combobox before the acceptance button is clicked. Use this when a test needs to transition an invitation from "pending" to "accepted" with specific metadata.

## Invariants

- **Requires a match pattern.** The `pattern` argument must uniquely identify the specific invitation row to avoid clicking the wrong item.
- **Position selection is conditional.** If `position` is provided, the method must first interact with the `combobox` (role: `combobox`) and select the option before clicking the accept button.
- **Visibility timeout.** The method enforces a 10,000ms visibility check on the row before attempting interaction to ensure the UI has settled.
- **Regex-based button matching.** The "accept" button is identified via a case-insensitive regex `/^accept$/i`.

## Gotchas

- **Implicit dependency on `itemFor(pattern)`.** If the `pattern` is too generic, the method may interact with the wrong row or fail due to multiple matches.
- **Order of operations.** The `combobox` interaction must happen *before* the final click on the accept button; failing to provide a `position` when one is required by the UI will result in a failed acceptance.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to view and interact with the notifications dropdown.
- **Side effects**: Successfully calling this will trigger a state change in the invitation lifecycle, which should be reflected in the user's active invitations or dashboard.

## External consumers

None known.
