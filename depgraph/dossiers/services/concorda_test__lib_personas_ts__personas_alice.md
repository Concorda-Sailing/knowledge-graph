---
node_id: concorda-test::lib/personas.ts::personas.alice
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 73ee8f07506b2aa7ea69a2feb77a3202c21af99d9394a8efb5c98c8a08e2de68
status: current
---

# personas.alice

## Purpose

Provides a pre-authenticated Playwright context for the "Alice" persona (Member). It uses the `asPersona` helper to wrap a browser instance with a specific `storageState` file, allowing tests to bypass manual login flows. Use this when a test requires a user with "Member" level permissions to interact with the UI or API.

## Invariants

- **Returns a `Persona` object** containing a `page` and a `close` method.
- **Uses `member.json`** as the source of truth for the authentication state.
- **Requires a `Browser` instance** to initialize the context.

## Gotchas

- **Persona identity is tied to a static file.** If the `member.json` state expires or the user's credentials change in the database, `personas.alice` will fail to provide a valid session.
- **The `asPersona` helper is the engine.** Any change to how `asPersona` handles the `Browser` or `storageState` path will directly impact the reliability of this persona.

## Cross-cutting concerns

- **Auth**: Uses the `member.json` auth state via `asPersona`.
- **Side effects**: Used in E2E specs to simulate user-level interactions, such as the co-owner Inbox flows added in commit `03a3cdd`.

## External consumers

None known.
