---
node_id: concorda-test::pages/events.page.ts::EventsPage.gotoSchedule
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d7ab9de6428f3e330237f0e90d9aed86a0fb9843863247f69de4f6cb9b79aa70
status: current
---

# EventsPage.gotoSchedule

## Purpose

Navigates the Playwright browser instance to the `/members/schedule` endpoint. This is a high-level navigation helper used to land the test runner on the member-facing schedule view. It is distinct from `gotoEvent(slug)`, which targets specific event detail pages, and should be used when the test needs to verify the general schedule listing or member-specific scheduling views.

## Invariants

- **Navigates to `/members/schedule`** — the hardcoded path for the member schedule view.
- **Waits for `networkidle`** — ensures the page is fully loaded and background API calls have settled before the next command in the test executes.

## Gotchas

- **Initial scaffolding only** — per commit `fd0c570`, this method is part of the initial E2E suite scaffolding and has not yet been subjected to complex edge-case testing or error-handling refinement.

## Cross-cutting concerns

- **Auth**: Requires a valid session (likely established via `LoginPage.goto` or similar) to access the `/members/` protected route.
- **Side effects**: Navigating here triggers the loading of the member schedule component.

## External consumers

None known.
