---
node_id: concorda-test::tests/dashboard/boats-panel.spec.ts::test@27
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: daa759cbc4418eeb25cd1aa1e82101c76c0e324b75c61dbf2945aa4631c549fd
status: llm_drafted
---

# owner sees their boat with Owner badge

## Purpose

Verifies that a boat owner sees the "Owner" badge on their boat card within the dashboard. This test ensures that the UI correctly distinguishes between a standard crew member and a boat owner by checking for the presence of the specific "Owner" text/badge.

## Invariants

- **Requires `boat-owner.json` storage state** — The test uses a specific `storageState` to simulate a user with ownership privileges.
- **Target URL is `/members?tab=boats`** — The test navigates to the specific tabbed view to ensure the boat panel is active.
- **Expects "Owner" text visibility** — The test asserts that at least one element with the text "Owner" (case-insensitive) is visible on the page.

## Gotchas

- **URL routing change** — Per commit `be406a9`, the test must account for the new `?tab=boats&boat=` URL pattern alongside legacy routes to ensure the panel renders correctly under the new routing logic.
- **Tab replacement** — Per commit `5720aac`, the dashboard has moved away from per-boat tabs to a unified boats panel; tests must now verify the existence of the "Owner" badge rather than looking for specific boat-id tabs.

## Cross-cutting concerns

- **Auth**: Uses `auth-states/boat-owner.json` to establish the authenticated session.
- **Side effects**: Verifies the visibility of the "Owner" badge, which is a key indicator of user role/ownership status in the dashboard UI.

## External consumers

None known.
