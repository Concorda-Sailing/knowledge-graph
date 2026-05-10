---
node_id: concorda-test::tests/boats/boat-resume.spec.ts::test@40
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fde878b70cad169b32b9c4c8b101b03e1c8569de5f0d4eedafa1cc79f7c6c976
status: llm_drafted
---

# can edit boat resume about field

## Purpose

Verifies the editability of the "About" field within the Boat Resume section. It ensures that a user can enter edit mode via the Profile card, modify the text area, and successfully persist changes using the explicit Save button. This test is distinct from general CRUD tests as it focuses specifically on the inline form interaction and the idempotency of the edit/revert cycle.

## Invariants

- **Requires an explicit Save button.** The test must click the button with the regex `/^save$/i` to commit changes.
- **Uses `textarea[id="about"]` for the input field.** The selector is specific to the boat's description field.
- **Idempotency via Reversion.** The test must revert the "about" field to its original value at the end of the test to prevent side effects on subsequent tests in the same worker.
- **Wait for `networkidle`.** Transitions between edit mode and view mode require waiting for the network to settle to ensure the UI state is stable.

## Gotchas

- **Form submission via Enter key.** Per commit `39a9fea`, the standalone page lacks a visible Save button in some configurations, requiring the test to use the explicit button or an Enter key press to avoid failures.
- **Navigation dependency.** Per commit `6a1bf88`, the test relies on the updated navigation pattern where the boat resume is accessed via the "Boats panel" rather than the removed per-boat tab.
- **Selector fragility.** Per commit `f552929`, selectors for the edit button and form fields were recently updated to align with the actual UI implementation to fix previous failures.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login` or a pre-seeded state) to access the Profile card and edit permissions.
- **Side effects**: Successful edits to the "about" field update the boat's profile data, which may be reflected in the boat-finder search results or overview displays.

## External consumers

None known.
