---
node_id: concorda-test::tests/finders/boatfinder.spec.ts::test@30
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9371b7c7fe8dfaebf3be65ba44cfb47ff45683bbf58561d1192c19ccf2cc8d1f
status: current
---

# can click on boat to view detail

## Purpose

Verifies the navigation flow from the Boat Finder list to the specific boat detail view. It ensures that clicking a boat card correctly triggers a view change and that the detail view displays the expected metadata (e.g., positions, crew status).

## Invariants

- **Navigation is conditional.** The test uses `if (await boatCard.isVisible())` to prevent hard failures if the test data (the "test breeze" boat) is missing from the search results.
- **Requires `networkidle` state.** After clicking the boat card, the test waits for `networkidle` to ensure the detail view has loaded data from the API.
- **Detail view content is semantic.** The test expects specific text patterns (`/about|positions|accepting crew|competitive/i`) to confirm the detail view is active.

## Gotchas

- **Flaky visibility checks.** The test uses a `5_000`ms timeout for the detail view visibility check, suggesting that the transition from the finder list to the detail view can be slow or subject to race conditions in the UI.
- **Implicit dependency on test data.** The test relies on a boat named "test breeze" being present in the search results; if the search index or seed data changes, this test will skip the assertion rather than failing.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Verifies the UI state for the boat-finder and boat-detail views.

## External consumers

None known.
