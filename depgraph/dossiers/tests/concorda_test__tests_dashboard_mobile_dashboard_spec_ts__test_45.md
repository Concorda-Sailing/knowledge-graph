---
node_id: concorda-test::tests/dashboard/mobile-dashboard.spec.ts::test@45
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ea7868c95b9f63c072d6abf9c9d1d6f88bfd8c38890f0d45c2edc28d772b88a1
status: llm_drafted
---

# hamburger is hidden on desktop

## Purpose

Verifies that the navigation hamburger menu is hidden when the viewport is set to desktop dimensions. This test ensures that the responsive design logic correctly suppresses the mobile-only navigation trigger on larger screens.

## Invariants

- **Viewport is fixed** — uses a width of 1280px and height of 800px to force the desktop layout state.
- **Uses `member.json` storageState** — relies on a pre-authenticated member session to bypass the login flow.
- **Target element is identified by accessibility label** — looks for the element with the label matching `/open navigation/i`.

## Gotchas

- **Regression-focused** — this specific test is part of a "desktop dashboard (regression)" block, implying that changes to the sidebar or navigation IA (Information Architecture) frequently break desktop visibility-of-elements.
- **Implicit dependency on `storageState`** — if `auth-states/member.json` is missing or malformed, the `page.goto('/members')` call will fail before the hamburger check can execute.

## Cross-cutting concerns

- **Auth**: Uses `storageState: 'auth-states/member.json'`.
- **Side effects**: Changes to the navigation component or sidebar IA (per commit `dc55160`) can cause this test to fail if the `getByLabel` selector is no longer valid or if the element is not correctly hidden via CSS.

## External consumers

None known.
