---
node_id: concorda-test::lib/personas.ts::personas.admin
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: db2cdf4f3dd8e8c56ed6bb951ba82930d1ed0a5fa678e2a6c8211aa4af9989e7
status: llm_drafted
---

# personas.admin

## Purpose

Provides a Playwright `BrowserContext` pre-authenticated as the system administrator. It is a specific instance of the `personas` object used to bypass standard user-level permission restrictions during E2E testing. Use this when testing administrative dashboards, global settings, or system-wide configurations that require elevated privileges.

## Invariants

- **Returns a `BrowserContext`** via the `asPersona` helper.
- **Relies on a physical file** located at `AUTH_STATES_DIR/admin.json`.
- **Requires a `Browser` instance** to be passed as an argument to initialize the context.

## Gotchas

- **Hard-coded state dependency:** This persona is not a dynamic login flow but a static injection of a `storageState`. If the `admin.json` file is not regenerated or is out of sync with the current database schema/auth provider, `personas.admin` will fail to provide the expected elevated permissions.
- **Recent addition:** Per commit `ab4d7ce`, this is part of a new pattern for multi-context testing; ensure any new persona added follows the `asPersona(browser, path.join(...))` pattern to maintain consistency with the `personas` object structure.

## Cross-cutting concerns

- **Auth**: Uses a pre-baked `storageState` (admin.json) to establish identity.
- **Side effects**: Used to test administrative-only UI elements and global system settings.

## External consumers

None known.
