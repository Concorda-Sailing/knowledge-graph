---
node_id: concorda-test::pages/invite-landing.page.ts::InviteLandingPage.accept
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b2dd3deec05c8e8eebc6c81a261a9ba8c9f0cc565378e35a2a22174834dd2955
status: llm_drafted
---

# InviteLandingPage.accept

## Purpose

The `accept()` method simulates a user clicking the primary call-to-action on the invite landing page. It transitions the user from the pending invitation state to the successful acceptance state. It is distinct from `clickSignUp` or `clickLogIn` as it specifically validates the transition to the `acceptedPanel`.

## Invariants

- **Requires an active invitation token** in the URL to function correctly.
- **Asserts visibility of `this.acceptedPanel`** immediately after the click to ensure the UI has transitioned.
- **Uses a 10,000ms timeout** for the visibility assertion, matching the pattern in `expectPendingView`.

## Gotchas

- **Recent implementation/refactor:** This method and the surrounding landing page object were part of the recent work in commit `b59e337`.

## Cross-cutting concerns

- **Auth**: Implicitly relies on the validity of the invitation token/session established by the landing page URL.
- **Side effects**: Successful execution triggers the transition from a "pending" state to an active user state for the invited entity.

## External consumers

None known.
