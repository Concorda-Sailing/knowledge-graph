---
node_id: concorda-test::tests/boats/boat-crud.spec.ts::test@69
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fef1e8bfb77d57ee96b4e23231824950260ad9f7bc7d6241ebebf3d20fb53116
status: llm_drafted
---

# can create a new boat

## Purpose

Tests the end-to-end lifecycle of boat creation within the `/members` dashboard. It verifies the UI flow of navigating to the "Add Boat" interface (via either a tab or a button) and successfully submitting a new boat record. This test is a critical part of the boat-crud regression suite to ensure the membership management UI remains functional.

## Invariants

- **Requires navigation to `/members`** before attempting to interact with the boat creation elements.
- **Uses a dynamic sail number** via `'TEST-NEW-' + Date.now()` to avoid collisions with existing records.
- **Relies on a fallback mechanism** for the "Add Boat" trigger, checking for both a `tab` and a `button` to accommodate different UI layouts.
- **Expects a visible "E2E Test Boat" text** in the DOM after the save operation completes.

## Gotchas

- **Heavy reliance on `page.waitForTimeout`** — the test uses hardcoded sleeps (1000ms and 2000ms) to wait for UI transitions and network stability. This makes the test brittle and prone to flakiness if the environment is slow.
- **Selector ambiguity** — the `sailInput` uses an `.or()` logic between a label and a placeholder. If the UI changes to a different labeling convention, this selector may fail to find the element.
- **Initial commit scaffolding** — per commit `fd0c570`, this is part of the initial E2E suite scaffolding; it may lack the robustness of production-grade tests and relies on the existence of the `/members` route.

## Cross-cutting concerns

- **Auth**: Implicitly depends on the authenticated state established in the global setup (likely via `ApiClient.login` or similar).
- **Side effects**: Creates a new boat record in the test database; ensure the test environment is reset or that the dynamic sail number prevents unique constraint violations.

## External consumers

None known.
