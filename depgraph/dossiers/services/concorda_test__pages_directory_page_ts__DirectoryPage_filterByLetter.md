---
node_id: concorda-test::pages/directory.page.ts::DirectoryPage.filterByLetter
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f31b982dbc21ac6245a303761f49a537731955b9c3531e2f245270c905e2e28e
status: llm_drafted
---

# DirectoryPage.filterByLetter

## Purpose

The `filterByLetter` method simulates a user clicking a single-letter navigation button in the member directory. It is used to narrow the directory view to a specific alphabetical index. This is distinct from `searchFor`, which interacts with the text input; `filterByLetter` specifically targets the alphabetical filter buttons.

## Invariants

- **Input is a single character string.** The method expects a single letter to construct the regex for the button click.
- **Uses a strict regex match.** The selector uses `^${letter}$` to ensure it clicks the exact button (e.g., clicking "A" won't accidentally click a button labeled "Ab").
- **Waits for `networkidle`.** Every call triggers a `waitForLoadState('networkidle')` to ensure the filtered list has finished loading before the test proceeds.

## Gotchas

- **Initial commit scaffolding.** Per commit `fd0c570`, this method is part of the initial E2E suite scaffolding; it is a high-level page object method and should be treated as a stable part of the test-side API.

## Cross-cutting concerns

- **Auth**: None (assumes the user is already on the `/members/directory` page via a previous navigation step).
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
