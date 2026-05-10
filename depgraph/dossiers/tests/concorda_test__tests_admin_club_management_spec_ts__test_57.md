---
node_id: concorda-test::tests/admin/club-management.spec.ts::test@57
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7d9502bdfc2a74e38104cc2056da0223ef7a77eb046b274295bed56aa8e49756
status: llm_drafted
---

# can click on club to edit

## Purpose

Verifies the ability to enter the edit flow for a club within the admin dashboard. It ensures that clicking the "edit" button on a club row successfully triggers the visibility of the name input dialog. This test is distinct from the search test above it, which focuses on record existence; this test focuses on the transition from the list view to the edit state.

## Invariants

- **Requires an existing club record** — The test relies on the club being present in the list (likely via the `E2E Test` search pattern established in the preceding test).
- **Dialog visibility is the success criteria** — The test passes only if `clubsPage.dialogNameInput` becomes visible within the 3,000ms timeout.
- **Must handle conditional button presence** — The test uses an `if (await editButton.isVisible())` guard, meaning it is designed to be non-failing even if the edit button is missing, provided the rest of the flow is reachable.

## Gotchas

- **Race condition on dialog appearance** — The test uses `await page.waitForTimeout(1000)` after clicking the edit button. This is a brittle workaround for the time it takes the dialog to mount in the DOM.
- **Initial commit scaffolding** — Per commit `fd0c570`, this file is part of the initial E2E suite scaffolding; the reliance on `waitForTimeout` suggests the UI-driven transitions are not yet fully deterministic in the current test environment.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (inherited from the `clubsPage` setup).
- **Side effects**: Successful interaction with the edit button and subsequent dialog visibility validates the `clubsPage.dialogNameInput` selector and the club-edit routing logic.

## External consumers

None known.
