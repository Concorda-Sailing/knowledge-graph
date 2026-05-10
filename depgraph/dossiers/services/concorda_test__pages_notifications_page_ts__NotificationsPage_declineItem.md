---
node_id: concorda-test::pages/notifications.page.ts::NotificationsPage.declineItem
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 659ec22fd1d9f1c7f1b4f04d92553141879d60c9e5cd30a554d87d3361462026
status: llm_drafted
---

# NotificationsPage.declineItem

## Purpose

The `declineItem` method is a Playwright-based Page Object Model (POM) helper used to reject an invitation or notification. It locates a specific row matching the provided `pattern` and clicks the "Decline" button. This is used in end-to-end tests to verify that users can successfully dismiss incoming requests and that the UI updates to reflect the declined state.

## Invariants

- **Input is a `RegExp` or `string`** — the pattern must uniquely identify the specific notification row to avoid clicking the wrong item.
- **Requires visibility before interaction** — the method explicitly awaits `toBeVisible` with a 10s timeout before attempting the click.
- **Target is a button with text `/^decline$/i`** — the selector is strictly tied to the case-insensitive "decline" text.

## Gotchas

- **Recent addition** — this method was introduced in commit `664f601` as part of the initial notification bell/dropdown page object implementation.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login`) to access the notification dropdown/bell.
- **Side effects**: Successfully calling this should trigger the removal of the item from the notification list and potentially update the unread count/badge in the UI.

## External consumers

None known.
