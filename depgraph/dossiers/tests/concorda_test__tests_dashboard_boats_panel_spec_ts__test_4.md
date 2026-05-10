---
node_id: concorda-test::tests/dashboard/boats-panel.spec.ts::test@4
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 17f9b8b5c62a04f6c75a389ca333a62fced317d3e732a91bb8a96816ab032e22
status: current
---

# Boats tab renders cards for owned + crewed boats

## Purpose

Verifies that the "Boats" tab in the member dashboard correctly renders boat cards for both members and owners. It ensures that the UI correctly distinguishes between a standard member view (showing crewed boats) and a boat-owner view (showing owned boats and the "Owner" badge). This test is critical for ensuring that the transition from legacy per-boat tabs to the new query-parameter-based navigation works without breaking the member-specific view.

## Invariants

- **URL structure must use `?tab=boats`** to trigger the correct panel view.
- **The "Owner" badge must be visible** when the `boat-owner.json` storage state is used.
- **The "My Crew" tab must be present** in the owner viewport but absent in the non-owner (member) viewport.
- **Boat links must use the new routing pattern** (either `href*="boat="` or `href^="/members/boats/"`) to be considered valid.

## Gotchas

- **Navigation change:** Per commit `5720aac`, the dashboard boats panel has replaced the old per-boat tabs. Tests must now account for the `?tab=boats` query parameter rather than looking for specific tab values like `boat-...`.
- **Routing compatibility:** Recent changes (commit `be406a9`) introduced a new URL pattern (`?tab=boats&boat=`) alongside the legacy route; ensure locators for boat links are broad enough to catch both.

## Cross-cutting concerns

- **Auth**: Uses `storageState: 'auth-states/boat-owner.json'` to simulate the owner-specific view.
- **Side effects**: Changes to the boat routing or the `?tab=boats` parameter will break this test.

## External consumers

None known.
