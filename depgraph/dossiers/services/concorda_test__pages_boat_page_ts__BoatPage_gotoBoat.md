---
node_id: concorda-test::pages/boat.page.ts::BoatPage.gotoBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3fb9c4124b2b754e42cd03d87dd13b5f6ac583bb26c8b7678469f0287f18bb4d
status: llm_drafted
---

# BoatPage.gotoBoat

## Purpose

Navigates the Playwright browser instance directly to a specific boat's detail page. This is the primary entry point for any test targeting boat-specific configurations, crew management, or boat-level punchlists. Use this instead of clicking through the dashboard or menu navigation to ensure tests are isolated and fast.

## Invariants

- **Requires a valid `boatId` string.** The method constructs a URL path using `/members/boats/${boatId}`.
- **Waits for `networkidle`.** The method explicitly waits for the network to be idle after navigation to ensure the page is fully loaded and data-fetching is complete before the test continues.

## Gotchas

- **Initial scaffolding state.** Per commit `fd0c570`, this method is part of the initial E2E suite scaffolding; ensure that any changes to the URL structure in the web app are reflected here immediately to avoid breaking the entire boat-related test suite.

## Cross-cutting concerns

- **Auth**: Relies on the session established by the `LoginPage` or `ApiClient` (the user must be authenticated to view `/members/boats/`).
- **Side effects**: Navigating here is a prerequisite for tests interacting with `this.punchlistItems` and `this.addPunchlistButton`.

## External consumers

None known.
