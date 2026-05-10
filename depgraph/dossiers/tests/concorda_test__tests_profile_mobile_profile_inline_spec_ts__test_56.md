---
node_id: concorda-test::tests/profile/mobile-profile-inline.spec.ts::test@56
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e7be5bdd380a263d2a8d4cd961cc3e451dcf3e7cf323b3e48591626bc1975158
status: llm_drafted
---

# all three tabs still render at desktop width

## Purpose

Verifies that the profile editing interface maintains correct layout behavior across different viewport widths. Specifically, it ensures that the "Personal Information" section transitions from a vertical stack on mobile to a horizontal side-by-side layout on desktop. This test prevents regressions where UI elements (like Save/Cancel buttons) might overlap or fail to align correctly when the screen expands.

## Invariants

- **Desktop Viewport Requirement**: The test explicitly sets `viewport: { width: 1280, height: 800 }` via `test.use` to ensure the desktop layout is triggered.
- **Horizontal Alignment**: The "Cancel" and "Save" buttons must be horizontally aligned, defined by a vertical distance of less than 5 pixels (`Math.abs(cBox!.y - sBox!.y) < 5`).
- **Tab Visibility**: All three profile tabs (Overview, Sailing Experience, Racing Preferences) must be visible and accessible when the desktop viewport is active.

## Gotchas

- **Layout Reflow Sensitivity**: Per commit `cb6d60e`, this test is sensitive to the "inline-edit + section reflow" logic. Changes to the CSS or the way the `personalCard` container handles its children can cause the button alignment assertion to fail.
- **XPath Dependency**: The test relies on a specific structural selector `xpath=ancestor::div[contains(@class, "rounded-xl") or contains(@class, "rounded-lg")][1]` to find the `personalCard`. If the UI component's wrapper class changes from `rounded-xl` to a different utility class, the test will fail to find the buttons.

## Cross-cutting concerns

- **Auth**: None (assumes authenticated session established by the test runner/setup).
- **Websocket**: None.
- **Audit**: None.
- **Rate limit**: None.
- **Side effects**: Verifies the visual state of the profile page, which is a prerequisite for any successful "Save" operation in the profile flow.

## External consumers

None known.
