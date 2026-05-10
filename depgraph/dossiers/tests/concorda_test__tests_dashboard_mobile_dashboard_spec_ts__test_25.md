---
node_id: concorda-test::tests/dashboard/mobile-dashboard.spec.ts::test@25
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 281cde5643f449421639a4b6d9c61ff94836b4580739ded437973c3b0e91c5c5
status: llm_drafted
---

# pending invite banner renders above first upcoming event

## Purpose

Verifies the visual stacking order of the "crew invitation" banner relative to the first upcoming event on mobile viewports. This ensures that if a pending invitation exists, the banner is rendered above the event list rather than overlapping or appearing below it.

## Invariants

- **Conditional Execution**: The test uses an `if (await banner.isVisible())` guard; if no banner is present (e.g., the test user has no pending invites), the test passes without asserting the Y-coordinate relationship.
- **Y-Axis Ordering**: If the banner is visible, the `bBox.y` (banner top) must be less than `eBox.y` (event top).
- **Locator Strategy**: Uses a regex `/crew invitation/i` to find the banner and a specific data-attribute `[data-slot="card"]` or class `.upcoming-event` to identify the event list.

## Gotchas

- **Mobile Viewport Sensitivity**: The test relies on the specific layout behavior of the mobile dashboard. Recent commit `dc55160` ("test(mobile): dashboard mobile viewport + sidebar IA cleanup") suggests the mobile layout and sidebar information architecture are actively being refined; changes to the sidebar or header height may impact the visibility of the banner or the event list.

## Cross-cutting concerns

- **Auth**: Uses standard Playwright `page` object; relies on the underlying test setup to provide a user state that may or may not have pending invites.
- **Side effects**: Changes to the mobile dashboard layout (specifically the sidebar or top navigation) can cause this test to fail if the banner is pushed out of the viewport or obscured.

## External consumers

None known.
