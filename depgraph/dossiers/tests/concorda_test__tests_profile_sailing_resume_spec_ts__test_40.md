---
node_id: concorda-test::tests/profile/sailing-resume.spec.ts::test@40
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 58a46b505a5f5949a93896338fbdea9cf1409a697cac4fad57b7f13047551438
status: llm_drafted
---

# can edit about me field

## Purpose

Verifies the ability of a user to modify the "About Me" text field within their sailing profile. This test ensures that the text input is interactive and that the subsequent "Save" action successfully persists changes to the user's profile data.

## Invariants

- **Input is a text field** labeled via `getByLabel(/about/i)`.
- **The test is conditional** on the visibility of the field; if the field is not present in the DOM, the test passes silently rather than failing.
- **Requires a manual revert step** to restore the `originalValue` after the test, ensuring the test environment remains in a known state for subsequent tests in the same run.

## Gotchas

- **Selector fragility:** Recent commits `7e8363c` and `f552929` highlight that this test is highly sensitive to the profile layout and the presence of "Tabs." The test relies on `page.getByLabel(/about/i)` and `page.getByRole('button', { name: /save/i })`, which may fail if the UI structure changes (e.g., moving from a single-page profile to a tabbed interface).
- **Race conditions:** The test uses a hardcoded `page.waitForTimeout(1000)` after clicking save. This is a brittle way to wait for the API/UI to settle and may lead to flaky results if the network or backend latency increases.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login` or a pre-seeded `storageState`) to access the profile editing surface.
- **Side effects**: Updates the user's profile record in the database; if the test fails to revert the "About Me" field, it may affect the state of the user for subsequent tests in the suite.

## External consumers

None known.
