---
node_id: concorda-test::tests/dashboard/boats-panel.spec.ts::test@16
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 03b85f8f74e5be0fae20fc792b1843f32946620601c12a534d8befbd6566d1a0
status: llm_drafted
---

# per-boat tabs are gone

## Purpose

Verifies that per-boat navigation tabs are correctly removed from the dashboard. This test ensures that the UI does not show specific boat-level tabs (e.g., `boat-123`) when the user is in a general view, preventing broken navigation or cluttered interfaces.

## Invariants

- **Tab value pattern**: The test specifically looks for `[role="tab"][value^="boat-"]` to ensure no element matches the legacy or per-boat routing pattern.
- **Navigation state**: The test assumes the user is on the `/members` route before asserting the absence of these tabs.

## Gotchas

- **Recent routing change**: Per commit `5720aac`, the "per-boat tabs" were replaced by a new system. This test exists to ensure that the legacy behavior (where tabs were generated for individual boats) does not regress or reappear.

## Cross-cutting concerns

- **Auth**: Uses the default test user (likely a non-owner or limited-permission user) to ensure the tabs are hidden for non-owners.
- **Side effects**: Ensures the "My Crew" tab visibility and the absence of boat-specific tabs are correctly handled in the dashboard layout.

## External consumers

None known.
