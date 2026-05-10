---
node_id: concorda-test::pages/invite-landing.page.ts::InviteLandingPage.expectErrorView
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 46215fc099effbd91491cc32af4310ed52fd7805ed79953bb87dec7a19139610
status: llm_drafted
---

# InviteLandingPage.expectErrorView

## Purpose

Verifies that the error state is correctly rendered on the invite landing page. This method is used when a user attempts to access an invite URL with an invalid or expired token, ensuring the UI provides appropriate feedback rather than a blank screen or a generic crash.

## Invariants

- **Asserts visibility of `this.errorText`** — the method specifically checks that the error message element is visible to the user.
- **Hardcoded 10s timeout** — uses a fixed `10_000`ms timeout for the visibility assertion to account for potential network latency during error state transitions.

## Gotchas

- **Recent implementation** — this method was part of the initial landing page object setup in commit `b59e337`.

## Cross-cutting concerns

- **Auth**: Relies on the failure of the invite token validation (the trigger for the error view).
- **Side effects**: None.

## External consumers

None known.
