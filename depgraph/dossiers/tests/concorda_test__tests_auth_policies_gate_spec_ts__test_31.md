---
node_id: concorda-test::tests/auth/policies-gate.spec.ts::test@31
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b00e158389bedfc146c5d81fb0f0e02cd69aa3b4aa51996a8d77a8030c93fbc3
status: current
---

# (unnamed)

## Purpose

This test acts as a regression gate for the global setup process. It iterates through a set of defined personas (admin, member, boat owners, etc.) to ensure that after `globalSetup` runs, no user is left with pending policy-acceptance requirements. It validates that the automated setup correctly satisfies the `/api/auth/accept-tos` requirement.

## Invariants

- **Persona-driven iteration**: The test loops through the `PERSONAS` array, ensuring every user type is validated.
- **Zero-pending policy requirement**: The expectation is strictly `[]` for the result of `api.getPendingPolicies()`.
- **Auth dependency**: Each test iteration performs a fresh `api.login(creds.email, creds.password)` to establish a clean session for that specific persona.

## Gotchas

- **Regression in global setup**: This test specifically guards against the failure mode identified in commit `c70d472`, where the setup process was attempting to hit a bogus `/auth/accept-tos` endpoint instead of the correct path.
- **Silent failure of `globalSetup.acceptTos()`**: If the setup logic fails to correctly satisfy the policy, this test will fail with a descriptive error message showing the actual pending policies.

## Cross-cutting concerns

- **Auth**: Uses `api.login` for each persona to establish identity before checking policy status.
- **Side effects**: Validates the state of the database/environment immediately following the execution of `globalSetup`.

## External consumers

None known.
