---
node_id: concorda-test::lib/personas.ts::asPersona
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ad2c1b6a8ded6021f3c693c36fc2dd8de420bc0af7fd0d09a5cfff2829083edc
status: current
---

# asPersona

## Purpose

Provides a factory for generating authenticated Playwright `BrowserContext` and `Page` instances using pre-seeded `storageState` files. It abstracts the complexity of manual state injection, allowing tests to quickly switch between specific user roles (e.g., `bob` for boat owners, `alice` for members) or test unauthenticated flows via `anonymous`.

## Invariants

- **Returns a `Persona` object** containing a `BrowserContext`, a `Page`, and a `close` method.
- **`statePath` is the source of truth for identity.** If `statePath` is provided, the context is initialized with that specific `storageState`.
- **`anonymous` bypasses state.** Calling `personas.anonymous()` passes `undefined` as the state path, resulting in a clean, unauthenticated browser context.
- **The `close` method is mandatory.** Users must call `persona.close()` to ensure the `BrowserContext` is destroyed and prevents memory leaks or context pollution between tests.

## Gotchas

- **Persona identity is tied to a static JSON file.** If a test requires a user with a specific permission set not covered by the hardcoded personas, a new JSON file must be generated in `AUTH_STATES_DIR` and a new key added to the `personas` object.
- **Recent addition via `ab4d7ce`.** This helper was introduced to support two-context tests (e.g., testing interactions between two different users), so older tests relying on manual context creation may need refactoring to use this pattern for consistency.

## Cross-cutting concerns

- **Auth**: Directly manages the injection of `storageState` for authenticated Playwright sessions.
- **Side effects**: Used to drive E2E specs for complex multi-user flows, such as the "Inbox accept/cancel flows" introduced in `03a3cdd`.

## External consumers

None known.
