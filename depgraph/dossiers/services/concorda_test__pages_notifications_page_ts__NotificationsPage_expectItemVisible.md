---
node_id: concorda-test::pages/notifications.page.ts::NotificationsPage.expectItemVisible
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4be175bf8067918df98a2caecc0a4f76ab8ee73cab71798f4a942649a841ad93
status: llm_drafted
---

# NotificationsPage.expectItemVisible

## Purpose

Provides a Playwright assertion to verify that a specific notification item (matching a string or regex pattern) is visible in the notification bell/dropdown. This is used to validate that an event or invitation has successfully reached the user's notification center. It is distinct from `expectItemGone`, which asserts the absence of an item after an action like `declineItem`.

## Invariants

- **Uses a 10-second timeout.** The assertion explicitly sets `{ timeout: 10_000 }` to allow for network/socket latency during notification delivery.
- **Relies on `this.itemFor(pattern)`** to locate the specific DOM element before asserting visibility.
- **Input is a `RegExp` or `string`.** The pattern must be specific enough to uniquely identify the notification row in the dropdown.

## Gotchas

- **Recent addition.** This method was part of the initial implementation of the notifications bell/dropdown page object in commit `664f601`.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: Likely depends on the notification websocket/event stream to trigger the visibility of the item being checked.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.
