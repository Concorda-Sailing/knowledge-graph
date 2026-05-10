---
node_id: concorda-test::tests/boats/boat-resume.spec.ts::test@66
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 63fedecb79326a218bac0124a99d863525390f2f89c9d85e99152f67b06454cd
status: llm_drafted
---

# publish toggle is visible on boat profile

## Purpose

Verifies that the "Publish/Visibility" toggle is visible and accessible within the boat profile edit mode. This test ensures that the UI transition from read-only to edit-mode correctly exposes the visibility controls, which are critical for controlling whether a boat appears in the public Boatfinder directory.

## Invariants

- **Requires Edit Mode activation.** The test must first click the "Edit Profile" button to expose the toggle; otherwise, the element is not present in the DOM.
- **Selector fallback.** The toggle is identified via a composite selector that looks for a `switch` role or specific text patterns (`publish`, `visible`, or `boatfinder`).
- **Timeout threshold.** The visibility assertion uses a 5,000ms timeout to account for the `networkidle` state and potential UI lag during the edit-mode transition.

## Gotchas

- **Selector fragility.** Per commit `f552929`, selectors must be carefully aligned with the actual UI to avoid silent failures in the E2E suite.
- **Navigation changes.** Per commit `6a1bf88`, the test relies on navigating via the "Boats panel" rather than the previously used per-boat tabs, which were removed.
- **Interaction requirement.** Per commit `39a9fea`, if the test were to interact with the form fields, it must handle the "Save" action via `Enter` or explicit button clicks, as the standalone page lacks a dedicated Save button in certain states.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login`) to access the boat profile edit routes.
- **Side effects**: Toggling this element affects the visibility of the boat in the public Boatfinder directory.

## External consumers

None known.
