---
node_id: concorda-test::pages/boat-crew.page.ts::BoatCrewPage.expectRowForName
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 32bb485bfc2a66cdfd8942b693b3378653a78d97d398ab609318995f098bc87f
status: current
---

# BoatCrewPage.expectRowForName

## Purpose

A specialized assertion helper for the Boat Crew page. It verifies that a specific person's row (represented by a card or list item) is visible and contains a specific status. It is used instead of generic locators to handle the non-deterministic rendering of names (e.g., whether the UI displays "First Last" or "Last, First") by using a partial name fragment.

## Invariants

- **Case-insensitive matching**: Both the `nameFragment` and the `status` are converted to `RegExp` with the `'i'` flag to ensure robust matching regardless of casing.
- **Strict visibility requirement**: The method must find a locator that satisfies both the name and status filters, or it will fail the `toBeVisible` assertion.
- **Selector fallback**: The locator searches across `a, div, li, tr` elements to ensure it can find the crew member regardless of whether they are in a table row or a card component.

## Gotchas

- **Implicit dual-filter requirement**: The method requires the element to match both the name and the status simultaneously. If the status is a string that appears elsewhere in the DOM (e.g., a global status indicator), the `first()` call might pick up the wrong element if the name match is not unique.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

None known.
