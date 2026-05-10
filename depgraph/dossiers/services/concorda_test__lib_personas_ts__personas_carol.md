---
node_id: concorda-test::lib/personas.ts::personas.carol
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0a61b41da9cb6ae18445f7266f56a4d068d6a5225810c903c044e60180ec9723
status: current
---

# personas.carol

## Purpose

Provides a pre-authenticated Playwright browser context for a user with the "crew-seeker" role. It wraps `asPersona` to load the specific auth state located at `crew-seeker.json` within the `AUTH_STATES_DIR`. Use this when testing flows that require a non-owner/non-admin perspective, such as browsing available boats or viewing public profiles.

## Invariants

- **Returns a Playwright `BrowserContext`** via the `asPersona` helper.
- **Uses a hardcoded auth state file** (`crew-json`) to ensure the persona is consistent across test runs.
- **Requires a `Browser` instance** as an argument to initialize the context.

## Gotchas

- **Auth state dependency**: The persona is only as valid as the `crew-seeker.json` file in the `AUTH_STATES_DIR`. If the global setup or `generateAuthState` fails to update this file, tests using `personas.carol` will fail with authentication errors.
- **Recent addition**: This persona was added in commit `ab4d7ce` as part of the new personas helper pattern; ensure any new persona-based tests follow the `asPersona` signature to avoid breaking the `personas` object structure.

## Cross-cutting concerns

- **Auth**: Relies on the `AUTH_STATES_DIR/crew-seeker.json` file for identity.
- **Side effects**: Used to drive E2E specs for user-facing features like the Inbox (per commit `03a3cdd`).

## External consumers

None known.
