---
node_id: concorda-test::pages/notifications.page.ts::NotificationsPage.expectUnread
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 393bb596ed7f547b295459cd56cf5bcd3f767ba2a53ef9fbc3de9730598a1ae1
status: current
---

# NotificationsPage.expectUnread

## Purpose

The `expectUnread` method asserts the visibility of the unread notification badge on the "My Schedule" tab. It is used to verify that a user has received a new invitation or notification that requires attention. This method is distinct from `expectNoUnread`, which asserts the absence of the badge, and should be used to validate the "active" state of the notification system without requiring the user to manually open the notification banner.

## Invariants

- **Relies on `this.unreadBadge` visibility** — The method passes if the element is visible within the 10,000ms timeout.
- **Does not require banner interaction** — Unlike full navigation flows, this assertion can be run while the user is on the main dashboard or schedule view.
- **Uses a hardcoded 10s timeout** — All visibility assertions in this class default to a 10,000ms timeout to account for asynchronous state updates.

## Gotchas

- **Recent implementation** — This method was introduced in commit `664f601` as part of the initial `NotificationsPage` POM setup.
- **Dependency on `this.unreadBadge` locator** — If the notification badge's CSS selector or DOM structure changes (e.g., moving from a `span` to a `div`), this assertion will fail even if the notification is logically present.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session where the user has active or pending invitations.
- **Websocket**: The visibility of the badge is often driven by real-time socket events; if the websocket connection is dropped or slow to propagate, this assertion may time out.
- **Side effects**: Success/failure of this assertion validates the end-to-end flow of the invitation system (e.g., after an admin sends an invite).

## External consumers

None known.
