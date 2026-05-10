---
node_id: concorda-test::tests/admin/club-management.spec.ts::test@21
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3b41660167e878903b3bc3d2e4902907d03f2052f5e073f80b23ece767fcf530
status: llm_drafted
---

# search filters clubs

## Purpose

Verifies the search filtering functionality on the Admin Clubs page. It ensures that entering a search term correctly narrows the visible list of clubs, preventing regressions in the club discovery UI.

## Invariants

- **Requires `clubsPage` fixture** — The test relies on the `clubsPage` Page Object Model to interact with the search input and the row count.
- **Expects a non-empty initial state** — The test assumes the existence of seeded data (via `expect(rows).toBeGreaterThan(0)`) to validate that the filter actually has items to act upon.
- **Uses a hard-coded delay** — The test explicitly waits for 1000ms after typing to allow the debounce/API call to settle before counting rows.

## Gotchas

- **Brittle debounce timing** — The test uses `await page.waitForTimeout(1000)` to wait for the search to complete. If the API or the frontend debounce logic exceeds this window, the row count assertion may fail or reflect the unfiltered state.
- **Dependency on seeded data** — Per the `clubs page loads with seeded organizations` test, this test will fail if the global setup fails to inject the ~50 seeded yacht clubs.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (handled by the `clubsPage` fixture/setup).
- **Side effects**: Verifies the visibility of the club list, which is a primary view for the Admin dashboard.

## External consumers

None known.
