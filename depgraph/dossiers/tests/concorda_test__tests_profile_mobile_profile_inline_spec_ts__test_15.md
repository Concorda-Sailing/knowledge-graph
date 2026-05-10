---
node_id: concorda-test::tests/profile/mobile-profile-inline.spec.ts::test@15
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 305c8fa04c8192333deab629e0dc7bc0f323317f8b63311a0e8b674ed2a3dfc4
status: llm_drafted
---

# tab bar does not wrap to two rows at 375px

## Purpose

Verifies the responsive layout and interaction patterns of the Member Profile page, specifically targeting mobile constraints. It ensures that the tab bar does not wrap to a second row at 375px and that the "Personal Information" section correctly transitions from a side-by-side button layout (desktop) to a stacked button layout (mobile) when entering edit mode.

## Invariants

- **Mobile viewport width is 375px** for mobile-specific layout assertions.
- **Tab bar height must be < 60px** to prevent vertical overflow/wrapping.
- **Button stacking is mandatory on mobile**: the `y` coordinate difference between the "Cancel" and "Save" buttons must be greater than 5px.
- **Horizontal overflow must be zero**: the document `scrollWidth` must not exceed 376px on the profile tab.

## Gotchas

- **Button alignment is sensitive to layout reflow**: Per commit `cb6d60e`, the "Personal Info" section was refactored to handle inline-edit and section reflow. This changed how buttons are positioned (stacked vs. side-by-side), making the `Math.abs(cBox!.y - sBox!.y)` check critical to prevent regressions in mobile stacking behavior.
- **XPath dependency for Card scoping**: The test relies on a specific XPath `ancestor::div[contains(@class, "rounded-xl") or contains(@class, "rounded-lg")][1]` to locate the `personalCard`. If the UI component structure changes (e.g., changing the rounding class), the `edit` and `save` buttons will become unreachable.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access `/members?tab=profile`.
- **Side effects**: Changes to the "Personal Information" section (via the `edit` button) affect the profile state, though this test only asserts visual/layout-based side effects.

## External consumers

None known.
