---
node_id: concorda-test::pages/notifications.page.ts::NotificationsPage.itemFor
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ed46bb982de20de1f57f11a2f6556bf96020da62cad328f65971371307d55407
status: llm_drafted
---

# NotificationsPage.itemFor

## Purpose

Provides a locator for a specific invitation row within the notifications banner. It filters the `this.banner` container for a `div` containing the provided `pattern` (string or RegExp), allowing tests to target specific event or boat names. This is the foundational selector used by `acceptItem`, `declineItem`, and visibility assertions to ensure the test interacts with the correct notification entry.

## Invariants

- **Returns a `Locator` object.** The output is a Playwright `Locator` and is not a terminal action; it must be passed to an action (like `.click()`) or an assertion (like `toBeVisible()`).
- **Scoped to `this.banner`.** The search is constrained to the notification banner element, preventing accidental selection of similar text in the main page body.
- **Selects the `.first()` match.** If multiple rows match the pattern, it returns the first one found.

## Gotchas

- **Pattern specificity matters.** Because it uses `.filter({ hasText: pattern })`, a generic pattern might match multiple rows or the wrong row if the pattern is too broad.
- **Dependency on `this.banner`.** If the notification banner's DOM structure changes (e.g., moving from a `div` to a `section` or changing the nesting level), this locator will fail to find the target row.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Used by `acceptItem` and `declineItem` to drive the state of the user's invitation list.

## External consumers

None known.
