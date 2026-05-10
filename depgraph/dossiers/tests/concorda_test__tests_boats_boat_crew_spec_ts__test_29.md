---
node_id: concorda-test::tests/boats/boat-crew.spec.ts::test@29
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 45f6020cb1da94b560ba6c2c62d326fb63e8897e11d910325ecca24f82ce7110
status: current
---

# can open invite crew dialog

## Purpose

Verifies the visibility and interaction of the crew invitation workflow within a boat's management interface. It ensures that the "Crew" tab can be accessed, the invitation dialog can be opened, and a user can successfully submit an email address to invite a new member. This test is distinct from the CRUD tests as it focuses on the transient UI state of the invitation modal and the subsequent success feedback.

## Invariants

- **Tab visibility is a prerequisite.** The test must first verify the `crewTab` is visible and click it before attempting to interact with the invite button.
- **Modal interaction requires explicit waits.** The test relies on `page.waitForTimeout(1000)` and `page.waitForTimeout(2000)` to account for the asynchronous rendering of the email input and the submission response.
- **Input selection is polymorphic.** The email field can be identified by either a `label` or a `placeholder` to accommodate different UI states or component versions.
- **Success state is text-based.** The test validates success by looking for the presence of the invited email or the string "success" in the DOM.

## Gotchas

- **Race conditions in UI transitions.** Per commit `0990b5d`, this test was added to cover `email-link` flows and includes `trace+screenshot` artifacts to debug timing issues where the `emailInput` might not be immediately interactable after clicking the invite button.
- **Implicit dependency on network idle.** The test uses `await page.waitForLoadState('networkidle')` after clicking the tab; if the network is noisy or a background polling-loop is active, this may hang or fail to trigger the next step.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login` or a pre-set `storageState`) to access the boat management tabs.
- **Side effects**: Successful execution of the "invite crew by email" step triggers a crew request/invitation in the backend, which may affect the "crew list" view for the invited user.

## External consumers

None known.
