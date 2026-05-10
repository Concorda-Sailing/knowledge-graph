---
node_id: concorda-test::tests/boats/boat-resume.spec.ts::test@34
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: becc4d3d2e97fe77cd73b52de0d6d0ac5ede1c29662add00343f8a43c8f4cfb1
status: current
---

# boat resume shows correct data

## Purpose

Verifies that the boat's "resume" data (about section, ethos, and visibility/publish status) is correctly rendered and editable. It ensures that the transition from "view mode" to "edit mode" via the profile edit button works and that changes to the `about` textarea are persisted to the backend.

## Invariants

- **Edit mode is required for visibility.** The `publish` toggle and the `about` textarea are only accessible/visible after clicking the `edit profile` button.
- **Form persistence requires an explicit save.** Changes to the `about` field are not auto-saved; the user must click the button with the regex `/^save$/i` to commit changes.
- **Idempotency via manual revert.** To prevent test pollution, the test manually reverts the `about` field to its `original` value and saves again at the end of the edit flow.

## Gotchas

- **Navigation/Routing dependency.** Per commit `6a1bf88`, the test relies on the boat being navigated via the "Boats panel" rather than the removed per-boat tab.
- **Selector fragility.** Per commit `f552929`, selectors were updated to align with the actual UI; specifically, the `CardTitle` is a `div`, not a heading, requiring location via the presence of the edit button.
- **Submit behavior.** Per commit `39a9fea`, the form must be submitted via an explicit Save button because the standalone page lacks the "Enter" key submission behavior found in other views.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `api.login` in a parent `describe` block) to access the boat profile.
- **Side effects**: Successful edits to the `about` field and the `publish` toggle update the boat's public-facing profile, affecting how the boat appears in global search/discovery.

## External consumers

None known.
