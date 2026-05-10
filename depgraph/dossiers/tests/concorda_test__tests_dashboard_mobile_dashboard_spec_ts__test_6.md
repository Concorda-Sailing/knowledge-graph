---
node_id: concorda-test::tests/dashboard/mobile-dashboard.spec.ts::test@6
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d16062adc29bb257578ac626f4cee4692a685aedf937ba3c437c7f937c929206
status: current
---

# hamburger visible on mobile; opens drawer

## Purpose

Verifies the mobile-specific layout and navigation of the member dashboard. It ensures the hamburger menu (Radix Sheet) is visible and functional at a 375x812 viewport, and validates that the tab list does not wrap or exceed a height of 60px. This test is distinct from the desktop regression tests in the same file, which explicitly check for the absence of the hamburger menu.

## Invariants

- **Viewport is fixed at 375x812** for the mobile-specific test block.
- **Uses `auth-states/member.json`** to provide a logged-in member context.
- **Sidebar visibility relies on `[data-sidebar="sidebar"]`** being the primary selector for the mobile drawer.
- **Tab list height must be < 60px** to prevent vertical overflow/wrapping on mobile screens.

## Gotchas

- **Banner visibility is conditional.** The "pending invite banner" test uses a conditional check (`if (await banner.isVisible()...`) because the presence of the banner depends on the specific user state in `member.json`. If the banner is missing, the test passes silently rather than failing, as noted in the source comment regarding Task 9.
- **Sidebar IA cleanup.** Recent changes in commit `dc55160` focused on mobile viewport and sidebar IA (Information Architecture) cleanup; ensure any changes to the mobile navigation structure do not break the `[data-sidebar="sidebar"]` selector.

## Cross-cutting concerns

- **Auth**: Uses `storageState: 'auth-states/member.json'`.
- **Side effects**: Verifies the rendering of the "pending invite banner" which is a transient UI element.

## External consumers

None known.
