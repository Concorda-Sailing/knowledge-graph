---
node_id: concorda-test::pages/crewfinder.page.ts::CrewfinderPage.gotoCrewDetail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f954d92ebff4feb9aa64d4dc9a069184c52408425680bdebd4b60b54adb8da32
status: llm_drafted
---

# CrewfinderPage.gotoCrewDetail

## Purpose

Navigates the Playwright browser instance directly to a specific crew member's detail page. This is used to bypass the manual search/filter steps required in the main Crewfinder view when a test needs to assert on a specific person's profile or contact capabilities.

## Invariants

- **Requires a valid `personId`** — the method expects a string that matches the URL pattern `/members/crewfinder/crew/{personId}`.
- **Waits for `networkidle`** — the method explicitly calls `await this.page.waitForLoadState('networkidle')` to ensure the profile data has finished loading before the test proceeds.
- **Directly manipulates the URL** — unlike `goto()`, which hits the base `/members/crewfinder` path, this method uses a template literal to construct a deep link.

## Gotchas

- **Initial scaffolding** — per commit `fd0c570`, this method is part of the initial E2E suite scaffolding and has not yet been subjected to edge-case testing for broken or non-existent `personId` values.

## Cross-cutting concerns

- **Auth**: relies on the authenticated state of the `page` instance; if the user is not logged in, the navigation will likely redirect to a login page.
- **Side effects**: none.

## External consumers

None known.
