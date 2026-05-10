---
node_id: concorda-test::tests/profile/mobile-profile-inline.spec.ts::test@63
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e3b70dc490292074b2740cd726ac1c66841ded195d7e5269a6de46a415116505
status: llm_drafted
---

# personal info save row is side-by-side on desktop

## Purpose

Verifies that the "Personal Information" section maintains a horizontal layout for the "Cancel" and "Save" buttons when the viewport is at desktop width. This ensures that the inline-edit reflow logic does not accidentally stack buttons vertically, which would break the desktop UI contract.

## Invariants

- **Viewport is fixed at 1280x800** via `test.use` to ensure the desktop-specific layout is triggered.
- **Buttons must be horizontally aligned.** The vertical distance (`y` coordinate) between the `cancelBtn` and `saveBtn` must be less than 5 pixels.
- **Requires an active edit state.** The test must click the `edit` button to trigger the transition from static text to the inline-edit row before asserting button positions.

## Gotchas

- **Layout sensitivity to reflow.** Per commit `cb6d60e`, this test is a direct check against regressions in the "inline-edit + section reflow" logic. If the section reflows incorrectly, the `y` coordinate delta will exceed the 5px threshold.
- **Selector fragility.** The test relies on a specific XPath/CSS structure (`ancestor::div[contains(@class, "rounded-xl")...]`) to locate the `personalCard`. Changes to the component's wrapper classes will break this test.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the `/members?tab=profile` route.
- **Side effects**: None.

## External consumers

None known.
