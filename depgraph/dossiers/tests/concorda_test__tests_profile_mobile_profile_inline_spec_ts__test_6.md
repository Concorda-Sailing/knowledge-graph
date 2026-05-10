---
node_id: concorda-test::tests/profile/mobile-profile-inline.spec.ts::test@6
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6b87efc6210a5d1b3de372ff318a5994f937e19aef6e50d141066c6ab3d7f6be
status: current
---

# overview tab renders all five sections

## Purpose

Verifies the responsive behavior of the profile overview tab across mobile and desktop viewports. It ensures that the profile sections (Member Directory, Crew Finder, Personal Information, Communications, and Security) render correctly and that the "Personal Information" inline-edit mode behaves differently based on screen width. Specifically, it validates that the Edit/Save buttons stack vertically on mobile (375px) but remain horizontally aligned on desktop (1280px).

## Invariants

- **Mobile Viewport** must be exactly 375x812 to test the mobile-specific button stacking logic.
- **Desktop Viewport** must be 1280x800 to ensure the regression test for side-by-side buttons passes.
- **Button Alignment** is the primary assertion for responsiveness; mobile requires a vertical offset (y-axis difference > 5px), while desktop requires horizontal alignment (y-axis difference < 5px).
- **Tab Visibility** is required for all five profile sections to ensure the `overview` tab is fully populated.

## Gotchas

- **Button Stacking Logic:** Per commit `cb6d60e`, the inline-edit mode was refactored to handle section reflow. The test relies on a specific XPath ancestor lookup (`ancestor::div[contains(@class, "rounded-xl") or contains(@class, "rounded-lg")][1]`) to scope the Edit/Cancel/Save buttons to the correct card container. If the card component's class structure changes, this locator will fail.
- **Mobile Overflow:** The test explicitly checks that `document.documentElement.scrollWidth` does not exceed 376px to prevent horizontal scrolling on the mobile profile view.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the `/members?tab=profile` route.
- **Side effects**: Changes to the profile section layout or the `Card` component's internal button-grouping logic will break the alignment assertions in this test.

## External consumers

None known.
