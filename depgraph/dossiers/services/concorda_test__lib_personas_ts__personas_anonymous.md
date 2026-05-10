---
node_id: concorda-test::lib/personas.ts::personas.anonymous
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ca0b6b9cbd091d8d5e4e1dac90c266ed01c3416dc5f45dbf61d6c0c2a8788ccd
status: current
---

# personas.anonymous

## Purpose

Provides a way to initialize a Playwright browser context without any authenticated state. While other personas in the `personas` object (like `bob` or `admin`) map to specific `storageState` JSON files to simulate logged-in users, `anonymous` calls `asPersona(browser, undefined)` to ensure a clean, unauthenticated session. Use this when testing public-facing routes or verifying that protected resources correctly return 401/403 errors.

## Invariants

- **Passes `undefined` as the second argument to `asPersona`** to bypass the loading of any auth state files.
- **Returns a Playwright `BrowserContext`** (via `asPersona`) that is strictly unauthenticated.
- **Does not rely on `AUTH_STATES_DIR`** for this specific persona, unlike the named personas in the same object.

## Gotchas

- **Implicitly unauthenticated.** Unlike the named personas (e.g., `bob`, `alice`) which are tied to specific `AUTH_STATES_DIR` paths, `anonymous` is the only persona that guarantees a lack of session data by passing `undefined`. If a test requires a "guest" state that isn't purely empty, this helper cannot be used.

## Cross-cutting concerns

- **Auth**: Generates a context with no bearer token or session cookies.
- **Side effects**: Used to verify that features like the "Inbox" (see commit `03a3cdd`) correctly restrict access to unauthenticated users.

## External consumers

None known.
