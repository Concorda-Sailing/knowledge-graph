---
node_id: concorda-test::tests/boats/mobile-boat-resume.spec.ts::test@17
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 71ccd8c9238f29ff444379107906454be01df86e7dbc0e5de858cc53ead9bc6a
status: current
---

# tab bar renders as a single scrollable row

## Purpose

Verifies the mobile-responsive layout of the boat detail view, specifically focusing on the horizontal tab bar and hero action buttons. It ensures that the navigation remains a single-row scrollable element and that critical UI components (like banner controls) are accessible without hover interactions on small viewports.

## Invariants

- **Viewport-specific dimensions**: The test suite uses a fixed viewport of `375x812` to simulate a standard mobile device.
- **Tab bar height**: The `tablist` bounding box height must be less than 60px to ensure it remains a compact, single-row pill bar.
- **Horizontal overflow**: For all active tabs (except 'overview'), the `document.documentElement.scrollWidth` must not exceed 376px to prevent unintended horizontal page scrolling.
- **Default tab behavior**: The 'overview' tab is the default active tab; clicking it is a no-op and is explicitly skipped in the loop to avoid flakiness.

## Gotchas

- **Tab click flakiness**: Per commit `a48c539`, the test must use `tab.scrollIntoViewIfNeeded()` and `tab.click({ force: true })` because the locator can become unstable when the tab is scrolled out of the horizontal `tablist` view.
- **Default tab skip**: The loop explicitly skips the click action for the 'overview' tab because it is already active by default; attempting to click it can cause failures in the test runner.
- **Profile tab removal**: Per the comment in the source, the 'profile' tab is no longer a top-level tab. Its content has been moved into the 'overview' tab within `boat-owner-view.tsx`.

## Cross-cutting concerns

- **Auth**: Relies on `goToFirstOwnedBoat(page)` to establish an authenticated session for a boat owner.
- **Side effects**: Ensures the "Add Banner" or "Change Banner" buttons are visible and interactable for owners without requiring hover states.

## External consumers

None known.
