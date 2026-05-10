---
node_id: concorda-test::tests/boats/boat-crud.spec.ts::test@46
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 12455fdfa505dfbd0e6b299ec3a3d1f11aa05b3907b6993a8c70c290d2932254
status: llm_drafted
---

# add boat dialog opens

## Purpose

Verifies that the "Add Boat" dialog/form is accessible and functional within the `/members` route. This test ensures that the UI transition from the member list to the creation form works, specifically checking for the presence of the sail number input. It serves as a prerequisite check for the full boat creation flow.

## Invariants

- **Navigation target is `/members`** — The test must start by navigating to the members directory to access the boat management UI.
- **Uses regex-based selectors** — The test relies on flexible regex (e.g., `/add.*boat|\+/i`) to find the trigger, as the UI may use either a tab or a button depending on the layout.
- **Requires `networkidle`** — The test waits for `networkidle` after navigation to ensure the member list and any dynamic UI elements are fully loaded before interaction.

## Gotchas

- **UI Flakiness/Race Conditions** — The test uses `page.waitForTimeout(1000)` and `page.waitForTimeout(2000)` to handle the transition between clicking the "Add Boat" trigger and the dialog appearing. This suggests the UI transition is not instantaneous or lacks a reliable state-change signal.
- **Dual-mode UI** — The "Add Boat" trigger can be either a `tab` or a `button` (per the `if (await addBoatTab.isVisible())` logic). This is a defensive pattern to handle different layout versions of the member dashboard.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (inherited from the test file's setup) to access the `/members` route.
- **Side effects**: Successful execution of the subsequent "can create a new boat" test (test@69) depends on this dialog opening correctly.

## External consumers

None known.
