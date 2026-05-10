---
node_id: concorda-test::tests/boats/coowner-request.spec.ts::test@7
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a32b16dd51da9731663b6ac9bc3757a161cfcf4c53b2e5b3ef237040c254d88e
status: llm_drafted
---

# shows sail-number conflict panel during registration

## Purpose

Verifies the UI-driven flow where a user attempts to register or add a boat that is already associated with an existing registration. It ensures the "already registered" conflict panel appears and that the user can successfully initiate a "Request co-owner" flow.

## Invariants

- **Requires specific seeded data** — The test relies on the existence of a boat with sail number `USA 12345` and name `Sirocco`.
- **Uses Playwright project-level auth** — Inherits `auth-states/boat-owner.json` via the `boat-owner` project configuration to simulate an authenticated session.
- **Expects visual feedback** — The "already registered" text and the "Request co-owner" button must be visible within a 5,000ms timeout.

## Gotchas

- **Currently skipped** — Both tests in this spec are explicitly skipped via `test.skip(true, ...)` because they require a specific seeded boat and a pending staging rollout.
- **Dependency on staging rollout** — Per commit `352aac8`, these tests are blocked until the deployment/seeding process is updated to support the required boat data.

## Cross-cutting concerns

- **Auth**: Uses the `boat-owner` Playwright project's `storageState` to provide an authenticated session.
- **Side effects**: Successful completion of the flow results in a "Pending request" banner appearing on the `/members` page.

## External consumers

None known.

## Open questions

- When will the seeding/deployment process be updated to allow these tests to be unskipped? (See commit `352aac8` for context).
