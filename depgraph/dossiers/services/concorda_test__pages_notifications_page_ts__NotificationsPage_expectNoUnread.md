---
node_id: concorda-test::pages/notifications.page.ts::NotificationsPage.expectNoUnread
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9ea225431d5d4f67f146bf2a9bc89e2582676595f7fa0014494d77349caaaacf
status: current
---

# NotificationsPage.expectNoUnread

## Purpose

The `expectNoUnread` method is a specialized assertion within the `NotificationsPage` POM used to verify the absence of unread notifications. It specifically checks that the `unreadBadge` element is hidden from the DOM or not visible to the user. This is typically called in the final stage of an invitation flow (after `acceptItem` or `declineItem`) to ensure the UI state has correctly transitioned from "pending" to "processed."

## Invariants

- **Relies on `this.unreadBadge` visibility** — The method asserts that the unread badge is hidden, not just that it has no text.
- **Uses a 10s timeout** — The assertion includes a hardcoded `10_000`ms timeout for the `toBeHidden` state.
- **Post-action verification** — This is intended to be called after a user action (like accepting an invite) that should trigger a state change in the notification center.

## Gotchas

- **Recent introduction** — This method was part of the initial implementation of the notifications bell/dropdown POM in commit `664f601`.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to view the notification bell/dropdown state.
- **Side effects**: Verifies the successful completion of invitation flows (Accept/Decline) which affects the visibility of the unread badge.

## External consumers

None known.
