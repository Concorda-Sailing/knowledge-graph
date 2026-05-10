---
node_id: concorda-test::setup/global-setup.ts::globalSetup
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f0dc21fda70a89bed070cd7e4702638c5bb8e82031a0d6f5d616b5c38321f46e
status: current
---

# globalSetup

## Purpose

The `globalSetup` function is the entry point for the Playwright E2E test suite's authentication lifecycle. It iterates through a predefined list of `AuthStateSpec` objects to generate and persist authenticated browser contexts (JSON files) for specific user personas. This ensures that tests can start with a pre-authenticated state rather than performing a fresh login in every single test file.

## Invariants

- **Iterates through `specs` array** to call `generateAuthState` for each user.
- **Persists state to `AUTH_STATES_DIR`** via the `statePath` property in each spec.
- **Uses `USERS` constants** for email and password credentials to ensure consistency with the test data library.
- **Returns `void`** and is intended to be run once before the test runner starts.

## Gotchas

- **Relies on pre-seeded host data.** Per commit `d7a3337`, the setup no longer performs local seeding and instead relies on a pre-seeded host. If the host environment is not pre-seeded with the required users, `generateAuthState` will fail for all personas.
- **Persona dependency.** The list of users (admin, alice, bob, carol, dan) is hardcoded. If a user is added to the test suite but not added to the `specs` array here, their `storageState` will not be available for Playwright projects.

## Cross-cutting concerns

- **Auth**: Generates the `storageState` files used by all authenticated Playwright tests.
- **Side effects**: The existence of these JSON files in `AUTH_STATES_DIR` is a prerequisite for any test that uses `storageState` in its project configuration.

## External consumers

- All Playwright E2E test projects in `concorda-test`.

## Open questions

- Should the `specs` array be moved to a configuration file or a dedicated constant file to avoid cluttering the setup logic as more personas are added?
