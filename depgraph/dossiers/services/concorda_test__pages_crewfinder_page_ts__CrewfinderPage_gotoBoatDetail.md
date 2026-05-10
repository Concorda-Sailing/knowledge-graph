---
node_id: concorda-test::pages/crewfinder.page.ts::CrewfinderPage.gotoBoatDetail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3ef67807f0f4c1f39525fe9c329c7f19909ab979a7cf96f1dfc85e570a63d5ed
status: current
---

# CrewfinderPage.gotoBoatDetail

## Purpose

Navigates the Playwright browser instance directly to a specific boat's detail page within the Crewfinder module. It is a specialized navigation helper for the `CrewfinderPage` class, used to bypass manual UI interactions when a test needs to inspect or manipulate a specific boat's data.

## Invariants

- **Requires a valid `boatId`** — the method expects a string that matches the application's boat identifier format.
- **Triggers a `networkidle` wait** — the method explicitly waits for the network to be idle after navigation to ensure the boat detail component has finished loading data from the API.
- **Direct URL manipulation** — it uses a template literal to construct the path `/members/crewfinder/boat/${boatId}`.

## Gotchas

- **Initial scaffolding state** — per commit `fd0c570`, this file is part of the initial Playwright E2E suite scaffolding; it lacks complex state-handling logic or specialized error recovery seen in more mature page objects.

## Cross-cutting concerns

- **Auth**: Relies on the authenticated state of the `CrewfinderPage` instance (likely established via a previous `LoginPage.goto` or `ApiClient.login` call).
- **Side effects**: Navigating here triggers the loading of the boat detail view, which may trigger API calls to fetch boat-specific crew lists.

## External consumers

None known.
