---
node_id: concorda-test::tests/finders/directory.spec.ts::test@30
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c54af06e30d9d11a7172070cc9879db386d117c3ff9e35283d56b7c28c83ea72
status: current
---

# search with no results shows empty state

## Purpose

Verifies the "empty state" behavior of the Directory search functionality. It ensures that when a user searches for a non-existent string (e.g., `ZZZNONEXISTENT`), the UI correctly displays a "no results found" message or an empty list rather than crashing or showing stale data.

## Invariants

- **Search input must be non-matching.** The test uses a high-entropy string (`ZZZNONEXISTENT`) to ensure no accidental matches occur with seeded data.
- **UI must show a fallback state.** The test expects either a specific text pattern (`/no.*found|no.*members|no.*results/i`) or an empty list state.
- **Asynchronous resolution.** The test relies on `page.waitForTimeout(1000)` to allow the search debounce/API round-trip to complete before asserting visibility.

## Gotchas

- **Brittle assertion logic.** The test uses `expect(hasNoResults || true).toBeTruthy();` which is a tautology that always passes. This suggests the "empty state" detection is currently non-deterministic or difficult to assert reliably with Playwright's `isVisible()`.
- **Manual timeouts.** The use of `page.waitForTimeout(1000)` indicates the search implementation likely has a debounce or a slow network round-trip that isn't being handled by a robust `waitForResponse` or `waitForSelector`.

## Cross-cutting concerns

- **Auth**: None (assumes user is already authenticated via the `directory` fixture).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
