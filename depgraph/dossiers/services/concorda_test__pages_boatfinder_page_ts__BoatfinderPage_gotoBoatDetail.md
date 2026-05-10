---
node_id: concorda-test::pages/boatfinder.page.ts::BoatfinderPage.gotoBoatDetail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cddd547f222ae9c1dac9b172db4e9167be798d27ab1c6d9a47006a22867d345a
status: llm_drafted
---

# BoatfinderPage.gotoBoatDetail

## Purpose

Navigates the Playwright browser directly to a specific boat's detail view using a `boatId`. This is the primary entry point for testing boat-specific configurations, crew lists, or status updates. Use this instead of `goto()` when a test needs to bypass the main Boatfinder list to verify deep-linked state or specific boat properties.

## Invariants

- **Requires a valid `boatId` string.** The method constructs a URL path `/members/boatfinder/${boatId}`.
- **Waits for `networkidle`.** The method explicitly calls `await this.page.waitForLoadState('networkidle')` to ensure the page is fully loaded and data-fetching is complete before the test proceeds.
- **Operates on the `page` instance.** It relies on the underlying Playwright page instance initialized in the constructor.

## Gotchas

- **Initial scaffolding only.** Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; ensure that any changes to the routing structure in the web app are reflected here to avoid broken navigation.

## Cross-cutting concerns

- **Auth**: None (assumes the user is already authenticated via a previous step in the test flow, such as `ApiClient.login` or a `storageState` injection).
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
