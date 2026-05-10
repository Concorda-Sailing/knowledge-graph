---
node_id: concorda-test::tests/dashboard/sidebar-ia.spec.ts::test@19
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eacbd812c87c3cf1b0b8406861dc07176106528bd24a77ddc2fd46b97b7f2d93
status: llm_drafted
---

# Finder navigates to /members/finder with crew tab selected

## Purpose

Verifies the navigation flow from the mobile dashboard sidebar to the Finder view. It ensures that clicking the "crew & boat finder" link correctly navigates to the `/members/finder` path and that the UI correctly initializes the "crew" tab as the active state.

## Invariants

- **Navigation target:** The URL must match the regex `/\/members\/finder(\?.*)?$/`.
- **Tab activation:** The `crew` tab must have the `aria-selected="true"` attribute and the `data-state="active"` state (via Radix UI) to be considered selected.
- **Modal handling:** The mobile drawer is a `role="dialog"`; the test must explicitly handle closing the drawer (via `Escape`) to interact with the underlying page content.
- **Hydration requirement:** The `tablist` must be explicitly waited for via `toBeVisible()` to account for client-side hydration/rendering delay after navigation.

## Gotchas

- **Mobile Drawer blocking:** The mobile drawer is a modal dialog. If the test does not handle the `Escape` key to close the menu, subsequent interactions with the `tablist` will fail because the drawer obscures the page.
- **Stabilization requirement:** Per commit `69f60cc`, the test requires an explicit wait for the `tablist` and an assertion on `aria-selected` to prevent flakiness during client-side hydration.

## Cross-cutting concerns

- **Auth**: Uses `storageState: 'auth-states/member.json'` for the legacy redirect tests in the same file.
- **Side effects**: Verifies the visibility of the "crew & boat finder" link, which is a primary entry point for the Finder feature.

## External consumers

None known.
