---
node_id: concorda-test::tests/boats/boat-crew.spec.ts::test@47
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f3abe3c9b8047644581e2fdb8ea665ad691d47ed98bee48e93b88cb7bcc5287e
status: llm_drafted
---

# invite crew by email

## Purpose

Verifies the crew invitation flow via email within the boat crew management interface. It ensures that a user can navigate to the crew tab, open the invitation dialog, and successfully submit an email address to invite a new member. This test is distinct from the standard "add crew" flow by specifically targeting the email-based invitation mechanism.

## Invariants

- **Navigation requires the Crew Tab to be visible** — the test checks for the existence of the `crew` tab before attempting to click it.
- **Email input must be reachable via label or placeholder** — the test uses a regex `/email/i` to find the input, accommodating different UI states.
- **Success is determined by text presence** — the test passes if the UI displays the invited email or a "success" message within a 5,000ms timeout.

## Gotchas

- **Requires explicit wait for UI stability** — the test uses `await page.waitForTimeout(1000)` and `2000` after clicking the invite button and the send button. This is necessary to allow the dialog animations/transitions to complete before attempting to fill or click.
- **Potential for flaky visibility checks** — the test relies on `if (await inviteButton.isVisible())` and `if (await emailInput.first().isVisible())`. If the UI is slow to render the modal, the test may skip the invitation logic entirely without failing, leading to a false positive.
- **Trace/Screenshot artifacts** — per commit `0990b5d`, this test is part of a recent effort to improve coverage for email-link flows and includes trace/screenshot artifacts for debugging failures.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely established via `api.login` in a parent `describe` block) to access the crew management features.
- **Side effects**: Successfully completing this test results in a new crew invitation record in the database, which should trigger an email to the invited address.

## External consumers

None known.
