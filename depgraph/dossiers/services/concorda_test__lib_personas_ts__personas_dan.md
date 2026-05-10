---
node_id: concorda-test::lib/personas.ts::personas.dan
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1aba41fcfb3f05e3e2f8a4a771df52bdc169e0994ef57ca19eab6071486e1a54
status: llm_drafted
---

# personas.dan

## Purpose

Provides a specific Playwright persona representing a second boat owner. It uses `asPersona` to load the `boat-owner-2.json` auth state, allowing tests to simulate multi-user scenarios where two distinct authenticated entities (e.g., two owners) interact with the same resource.

## Invariants

- **Uses `boat-owner-2.json`** — the persona is strictly tied to this specific auth state file in `AUTH_STATES_DIR`.
- **Requires a `Browser` instance** — the function signature `(browser: Browser) => ...` must be respected to initialize the persona context.
- **Returns a Playwright context/page wrapper** — via `asPersona`, providing the authenticated session for the second owner.

## Gotchas

- **Persona identity is tied to a static JSON file** — unlike `ApiClient.login`, this does not perform a live login; it relies on the existence of `boat-owner-2.json`. If the underlying user data in the DB changes, this persona may become stale or invalid.
- **Recent addition** — per commit `ab4d7ce`, this is part of a new pattern for "two-context tests." Ensure any new tests requiring dual-owner logic use this rather than attempting to manually manage two `ApiClient` instances.

## Cross-cutting concerns

- **Auth**: Uses a pre-generated auth state from `boat-owner-2.json`.
- **Side effects**: Used by `coowner-inbox.spec.ts` to test acceptance/cancel flows between two distinct owners.

## External consumers

None known.
