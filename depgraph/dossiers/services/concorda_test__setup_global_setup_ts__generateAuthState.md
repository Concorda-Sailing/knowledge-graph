---
node_id: concorda-test::setup/global-setup.ts::generateAuthState
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bca9b65442ce2f42d3cf24ce442eacabee7aea1fcb415e851d37b615482e1247
status: current
---

# generateAuthState

## Purpose

Generates Playwright `storageState` JSON files by simulating a full login flow and accepting the Terms of Service (TOS). This ensures that E2E tests can start in an authenticated state without manually handling the "Accept TOS" gate or repetitive login logic. It is distinct from `ApiClient.login` because it also performs the browser-level `localStorage` injection and `acceptTos()` call required to bypass the initial dashboard blockers.

## Invariants

- **Requires a valid `spec.email` and `spec.password`** that match existing users in the test environment.
- **Writes to a specific file path** defined by `spec.statePath` via `context.storageState`.
- **Injects the token into `localStorage`** under the key `'auth_token'` to ensure the session persists when the browser context is loaded by a test.
- **Uses `chromium` for generation** to ensure the resulting state file is compatible with the Playwright `chromium` project settings.

## Gotchas

- **Tolerates missing personas** — per commit `c00e870`, the function is designed to be host-agnostic; if a user/persona is missing or the login fails, it catches the error and logs a warning rather than crashing the entire global setup.
- **Relies on pre-seeded host data** — per commit `d7a3337`, this function no longer performs local database seeding; it assumes the `USERS` object contains credentials for users that already exist on the target host.
- **Implicitly handles the TOS gate** — the `try/catch` around `api.acceptTos()` is critical because certain personas (like those in the `admin` or `member` roles) may have already accepted terms, or the endpoint may reject the call for specific roles.

## Cross-cutting concerns

- **Auth**: Directly generates the `storageState` used by all authenticated Playwright tests.
- **Side effects**: The `globalSetup` loop populates the `AUTH_STATES_DIR` with files like `admin.json`, `member.json`, and `boat-owner.json`, which are then consumed by the `dashboard` and `race-management` test projects.

## External consumers

- Playwright E2E test suites (e.g., `dashboard.spec.ts`, `race-management.spec.ts`) that use `storageState` in their project configuration.
