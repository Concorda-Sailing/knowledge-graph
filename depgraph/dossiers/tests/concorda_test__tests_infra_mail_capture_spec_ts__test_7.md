---
node_id: concorda-test::tests/infra/mail-capture.spec.ts::test@7
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5acc578b7d63c11eb4b9276b699e696a4014020a2886e6e24bacc621ab136862
status: current
---

# forgot-password email is captured

## Purpose

This test verifies that the password reset flow successfully triggers an email that is intercepted by the `mailCapture` utility. It ensures that the `forgotPassword` action on the `ApiClient` results in a detectable, non-empty email body matching the expected recipient and subject pattern. This is a critical infra test for validating the end-to-end delivery of transactional emails during authentication failures.

## Invariants

- **Relies on `mailCapture.snapshot()`** to initialize the capture state before the action is triggered.
- **Requires `USERS.alice.email`** to be a valid, seeded user in the test environment.
- **Expects a regex match** on the subject line (`/reset|password/i`) to confirm the correct email type was sent.
- **Asserts on `msg.body.length`** to ensure the email is not just sent, but contains the actual reset content.

## Gotchas

- **Commit `06fb546`** introduced this test alongside the `mail-capture` helper; it serves as the baseline validation for the new capture logic.

## Cross-cutting concerns

- **Auth**: Indirectly tests the `forgotPassword` flow which is a precursor to authenticated sessions.
- **Side effects**: Validates the successful execution of the password reset email trigger in the backend.

## External consumers

None known.
