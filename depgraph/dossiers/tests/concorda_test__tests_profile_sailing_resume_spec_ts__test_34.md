---
node_id: concorda-test::tests/profile/sailing-resume.spec.ts::test@34
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5fa6b663680e8da19fe9a6e77f0ddb94eb1bd1172148159cc94ae7b474aa7ec7
status: llm_drafted
---

# can view preferred positions

## Purpose

Verifies that the "Preferred Positions" section of the user's sailing resume renders correctly. It ensures that seeded data (specifically for the user "Alice") is visible in the UI, preventing regressions in the profile display layer.

## Invariants

- **Regex-based matching**: Uses a case-insensitive regex (`/trimmer|bowman|pit|tactician|helm/i`) to validate the presence of position text.
- **Seeded data dependency**: Relies on the specific seeded values for "Alice" (positions "Trimmer, Bowman") to pass.
- **Visibility timeout**: Asserts that the element is visible within a 5,000ms window.

## Gotchas

- **UI Layout Changes**: Recent commit `7e8363c` and `552929` indicate that the profile structure has been volatile, specifically regarding the removal of "inner profile Tabs." Tests must use selectors that account for the current flat or updated layout to avoid false negatives.
- **Regex sensitivity**: The test relies on a broad regex to find position content; if the UI changes the way roles are listed (e.g., moving to a dropdown or a different text format), this test may fail or become too permissive.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient` or `storageState`) to access the profile view.
- **Side effects**: Changes to the profile layout or the way "Preferred Positions" are stored in the database will break this test.

## External consumers

None known.
