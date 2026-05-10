---
node_id: concorda-test::pages/crewfinder.page.ts::CrewfinderPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c16e17b15cc975bd2829e4584bf73fbfe5591e3347d50b9056ad2b8dac9ac7d0
status: current
---

# CrewfinderPage.goto

## Purpose

Navigates the Playwright browser to the Crewfinder page or specific detail views. This is the primary entry point for tests targeting the member directory, allowing an agent to move from a generic authenticated state into the specific UI context of a person or a boat.

## Invariants

- **Uses `networkidle`** — Every `goto` call waits for the `networkidle` state to ensure the member list or detail view is fully populated before the test proceeds to assertions.
- **Path-based routing** — Navigates to `/members/crewfinder` for the main list, or appends `/crew/${personId}` or `/boat/${boatId}` for detail views.
- **Requires an active session** — This method assumes the browser context is already authenticated; it does not handle login-related redirects.

## Gotchas

- **Initial scaffolding** — Per commit `fd0c570`, this method is part of the initial E2E suite scaffolding and currently lacks complex error handling for failed navigations.

## Cross-cutting concerns

- **Auth**: Requires a valid session/token established by a previous step (e.g., `LoginPage.login`).
- **Side effects**: Navigating to detail views triggers the loading of member/boat profile data from the API.

## External consumers

None known.
