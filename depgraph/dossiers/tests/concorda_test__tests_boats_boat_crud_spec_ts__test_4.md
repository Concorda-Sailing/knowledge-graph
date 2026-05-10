---
node_id: concorda-test::tests/boats/boat-crud.spec.ts::test@4
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4ce9d15eb6622849e59a353a973e96158e79461d5aab73a7d315c18e71334475
status: current
---

# dashboard loads for boat owner

## Purpose

Verifies that a boat owner can successfully access and interact with the boat management dashboard. This test ensures that the "Boat" tab or "Add Boat" functionality is visible and accessible within the `/members` route. It serves as a baseline for verifying that UI components (tabs, buttons, and dialogs) render correctly for authenticated users with boat-related permissions.

## Invariants

- **Requires navigation to `/members`** — the test must hit the members route to trigger the loading of the boat management interface.
- **Relies on `networkidle`** — the test uses `page.waitForLoadState('networkidle')` to ensure the heavy component tree and any initial API fetches are complete before asserting visibility.
- **Uses regex-based selectors** — selectors for tabs and buttons (e.g., `/test breeze|boat/i`) are case-insensitive and flexible to accommodate minor UI text changes.

## Gotchas

- **UI Ambiguity** — the "Add Boat" functionality can be triggered by either a tab named `add.*boat|\+` or a button named `add.*boat|new.*boat`. Tests must handle both possibilities via `if/else` or `.or()` logic to avoid brittle failures.
- **Initial Commit Scaffolding** — per commit `fd0c570`, this is part of the initial Playwright E2E suite scaffolding; it may lack deep assertion coverage for edge cases in the boat creation flow.

## Cross-cutting concerns

- **Auth**: Implicitly depends on the authenticated state of the browser context (likely established via a global setup or previous test in the suite).
- **Side effects**: Successful execution of the "create" flow (if extended) would impact the boat list visibility in the `/members` dashboard.

## External consumers

None known.
