---
node_id: concorda-test::tests/admin/event-management.spec.ts::test@15
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7a288a4ecd2a60e65bba99d6ad23dc96589664a5c7c082765056f48661a13ea6
status: llm_drafted
---

# series page loads

## Purpose

Verifies the loading and navigation of the "Series" page within the Admin Events dashboard. It ensures that the `AdminEventsPage` abstraction correctly navigates to the `/members/admin/events/series` route and that the page is responsive and accessible to an authenticated administrator.

## Invariants

- **URL Pattern**: The page must resolve to the specific path `/\/members\/admin\/events\/series/`.
- **Page Object Dependency**: Relies on `AdminEventsPage` to encapsulate navigation logic and element selectors.
- **Authentication**: Assumes the test runner has already established an admin session via a previous setup step.

## Gotchas

- **Selector Fragility**: Recent history shows a need to align selectors with the actual web UI (commit `7e8363c`). If the `AdminEventsPage` or the underlying React components change their structure (e.g., moving from Tabs to a different navigation pattern), this test is prone to breaking.
- **Setup Dependency**: Per commit `f552929`, the test relies on a specific setup to ensure the first run is "green." If the global setup or the `AdminEventsPage` initialization fails to provide a valid authenticated state, the navigation will fail.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session to access the `/members/admin/` route.
- **Side effects**: Successful navigation and interaction in this suite (and adjacent tests in this file) can impact the state of the test database, specifically regarding the creation of event records.

## External consumers

None known.
