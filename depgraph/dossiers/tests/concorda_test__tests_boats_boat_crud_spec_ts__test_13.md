---
node_id: concorda-test::tests/boats/boat-crud.spec.ts::test@13
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2380555d568797fc810ec027da9e0c70456a86c1f5d4a4daace41462ee4c8623
status: current
---

# can navigate to boat detail page

## Purpose

Verifies the end-to-end navigation flow for boat details within the `/members` dashboard. It ensures that a user can successfully navigate from the main dashboard to a specific boat's detail view and that the UI correctly renders boat-specific information (like sail number and name) once the view is loaded.

## Invariants

- **Navigation relies on `networkidle`** — The test must wait for `page.waitForLoadState('networkidle')` after navigating to `/members` to ensure the dashboard state is stable before attempting to click the boat tab.
- **Tab selection is conditional** — The test checks for both a "boat tab" and a "boat button" (via `add.*boat|\+/i`) to account for different UI implementations of the navigation trigger.
- **Content visibility is verified via regex** — The test expects to see specific text like `TEST-001` or `Test Breeze` to confirm the detail page has loaded correctly.

## Gotchas

- **Race conditions on tab clicks** — The test uses `await page.waitForLoadState('networkidle')` immediately after clicking the boat tab to prevent the test from attempting to find `boatContent` before the navigation completes.
- **Fragile selector for boat content** — The test relies on `page.getByText(/test breeze|TEST-001/i)` to confirm successful navigation; if the test data in the seed changes, this test will fail despite the navigation logic being correct.

## Cross-cutting concerns

- **Auth**: Assumes the user is already authenticated via the global setup/session (standard for `concorda-test` E2E flows).
- **Side effects**: Success in this test validates the visibility of the boat detail view, which is a prerequisite for other boat-related CRUD operations.

## External consumers

None known.
