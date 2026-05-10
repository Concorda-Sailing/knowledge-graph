---
node_id: concorda-test::pages/notifications.page.ts::NotificationsPage.expectItemGone
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b0840002e373aabe3fd273593cfac546935a7a14289d3f3bb38285990ade4dda
status: llm_drafted
---

# NotificationsPage.expectItemGone

## Purpose

The `expectItemGone` method asserts that a specific notification item (identified by a regex or string pattern) is no longer visible in the UI. It is the inverse of `expectItemVisible` and is used to verify that an invitation has been successfully dismissed, responded to, or removed from the notification dropdown/bell.

## Invariants

- **Uses `toBeHidden`** — The assertion checks for the absence of the element in the DOM or its invisibility, not just its non-existence.
- **Hardcoded 10s timeout** — The method explicitly sets a `{ timeout: 10_000 }` for the visibility check, ensuring the test waits for asynchronous UI updates (like a dismissal animation) before failing.
- **Input is a pattern** — Accepts a `RegExp` or `string` to locate the specific notification item within the list.

## Gotchas

- **Recent addition** — This method was introduced in commit `664f601` as part of the initial implementation of the notifications bell/dropdown page object.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: Assumes the UI has reacted to a websocket event (e.g., an invitation being deleted or status changing) that triggers the removal of the item from the DOM.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: None.

## External consumers

None known.
