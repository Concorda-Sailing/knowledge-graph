---
node_id: concorda-test::tests/finders/directory.spec.ts::test@52
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4a42fbf7beb5af923c535a7d73c1259a8ac8b1bc3871faaf330b40b69dee75fd
status: llm_drafted
---

# view toggle works

## Purpose

Verifies the UI state transition between "List" and "Grid" view modes within the Directory finder. It ensures that the user can toggle between these two layout representations without the application crashing or losing state.

## Invariants

- **Requires both buttons to be visible** — The test only executes the toggle logic if both the `grid` and `list` buttons are present in the DOM.
- **Uses regex-based selection** — Relies on `getByRole('button', { name: /grid/i })` and `/list/i` to find the toggle controls.
- **Implicitly assumes a stable layout** — The test relies on `page.waitForTimeout(500)` to allow the DOM to settle after a click, assuming the view transition is not instantaneous.

## Gotchas

- **Initial commit scaffolding** — Per commit `fd0c570`, this test is part of the initial Playwright E2E suite scaffolding; it is a high-level smoke test and may not catch granular CSS layout regressions.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
