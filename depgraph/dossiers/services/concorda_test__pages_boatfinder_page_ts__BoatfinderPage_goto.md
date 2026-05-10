---
node_id: concorda-test::pages/boatfinder.page.ts::BoatfinderPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5df89e37a8164018deed4381d851cb4e5e55b814af5c4cd4bad72a605a21cadd
status: llm_drafted
---

# BoatfinderPage.goto

## Purpose

Navigates the Playwright browser to the Boatfinder member view. It provides two distinct entry points: the main directory view via `goto()` and a specific boat detail view via `gotoBoatDetail(boatId)`. This ensures the browser is at the correct URL and the network is idle before the test attempts to interact with boat cards or application forms.

## Invariants

- **Uses `networkidle`** — both methods await `page.waitForLoadState('networkidle')` to ensure the boat list or detail data has finished loading before the test proceeds.
- **URL structure** — `goto()` targets `/members/boatfinder`, while `gotoBoatDetail` appends the `boatId` to the base path.
- **Implicitly requires authentication** — because this is a `/members/` route, the `ApiClient` or `storageState` must be established before calling this, or the navigation will likely redirect to a login page.

## Gotchas

- **Initial scaffolding** — per commit `fd0c570`, this is part of the initial E2E suite scaffolding; it has not yet been subjected to complex edge-case testing or refactoring.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login`) as it navigates to a protected `/members/` route.
- **Side effects**: Navigating here is the prerequisite for testing the "Apply to Boat" flow, which involves the `applyMessageInput` and `submitApplyButton`.

## External consumers

None known.
