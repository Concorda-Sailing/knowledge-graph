---
node_id: concorda-test::pages/notifications.page.ts::NotificationsPage.open
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 68a0be326451ddb3759a66f812ff040e744baa3210a4201d9da46fbf8d46df21
status: current
---

# NotificationsPage.open

## Purpose

The `open()` method ensures the test browser is positioned on the `/members` route with the `schedule` tab active. This is a prerequisite for interacting with in-app notifications, such as accepting or declining event invitations. It is used to establish a known state before asserting on the visibility of the unread badge or interacting with specific invitation rows.

## Invariants

- **Navigation is idempotent.** If the current URL already contains `/members`, it attempts to click the `scheduleTab` rather than performing a full page reload.
- **Requires `/members` context.** The method relies on the existence of the `scheduleTab` locator and the `banner` locator to verify successful navigation.
- **Hardcoded timeout.** The method uses a 10,000ms timeout for the `expect(this.banner).toBeVisible` assertion to account for network latency during tab switching.

## Gotchas

- **Navigation side-effects.** Because `open()` may trigger a `page.goto('/members?tab=schedule')`, it can reset the state of other UI components that rely on the current URL or tab state.
- **Implicit dependency on `scheduleTab`.** If the user is already on a sub-route of `/members` that does not expose the `scheduleTab` (e.g., a different sub-view), the `click()` action may fail or behave unexpectedly.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the `/members` route.
- **Side effects**: Successful interaction with items via `acceptItem` or `declineItem` will trigger updates to the user's event participation status in the backend.

## External consumers

None known.
