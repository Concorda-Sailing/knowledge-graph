---
node_id: concorda-test::tests/profile/mobile-profile-inline.spec.ts::test@45
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5e5f58295d6fc0d8054d837dc7f33adcae62ef95a9fbd48efef13bf70e4ce918
status: current
---

# no horizontal overflow on profile tab

## Purpose

Verifies that the profile tab maintains a responsive layout without horizontal overflow on mobile viewports. It ensures the UI remains usable on narrow screens by checking that the document width does not exceed a specific threshold (376px) when the profile tab is active.

## Invariants

- **Viewport width constraint:** The `document.documentElement.scrollWidth` must remain $\le$ 376px to prevent horizontal scrolling on mobile.
- **Heading visibility:** The "Personal Information" heading must be visible to confirm the correct tab state before measuring width.
- **Mobile-specific layout:** This test is part of a suite that distinguishes between mobile (stacked buttons) and desktop (side-by-side buttons) layouts.

## Gotchas

- **Layout regression:** Per commit `cb6d60e`, this test is sensitive to the "inline-edit + section reflow" logic. Changes to how profile sections reflow or how the mobile viewport is simulated can cause the `scrollWidth` check to fail if elements bleed past the 376px boundary.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the `/members?tab=profile` route.
- **Side effects**: Changes to the profile layout or the mobile-specific CSS/component structure will directly impact the `scrollWidth` assertion.

## External consumers

None known.
