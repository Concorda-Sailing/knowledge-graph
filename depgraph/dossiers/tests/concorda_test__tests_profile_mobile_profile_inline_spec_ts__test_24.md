---
node_id: concorda-test::tests/profile/mobile-profile-inline.spec.ts::test@24
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a434c196879e2f99662bb29bf3844e98873a9f4495a321ed916ecae781113440
status: current
---

# personal info edit toggle works; save row stacks

## Purpose

Verifies the layout behavior of the "Personal Information" section during inline editing. It ensures that the UI correctly transitions between mobile (stacked buttons) and desktop (side-by-side buttons) modes. This test is critical for preventing regressions in the responsive reflow logic of the profile card.

## Invariants

- **Mobile view requires vertical stacking**: When the viewport is narrow, the `cancel` and `save` buttons must have a vertical offset (`y` difference) greater than 5px.
- **Desktop view requires horizontal alignment**: When the viewport is wide (1280px), the `cancel` and `save` buttons must be horizontally aligned (y difference less than 5px).
- **Button selection is context-specific**: The test must use the `ancestor::div` XPath to scope the `edit`/`cancel`/`save` buttons to the specific "Personal Information" card to avoid picking up buttons from other profile sections.

## Gotchas

- **Layout reflow is sensitive**: Per commit `cb6d60e`, the inline-edit and section reflow logic was recently refactored. Changes to the CSS or the container's `rounded-xl`/`rounded-lg` classes can break the `personalCard` locator or the button stacking assertions.
- **XPath dependency**: The test relies on a specific DOM structure (`ancestor::div[contains(@class, "rounded-xl") or contains(@class, "rounded-lg")][1]`) to find the card container. If the UI library changes the rounding class or the nesting depth, the `personalHeading.locator` will fail to find the buttons.

## Cross-cutting concerns

- **Auth**: None (relies on the `/members?tab=profile` route which assumes a session is established via `ApiClient.login`).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

None known.
