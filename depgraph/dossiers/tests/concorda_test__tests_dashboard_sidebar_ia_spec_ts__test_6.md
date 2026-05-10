---
node_id: concorda-test::tests/dashboard/sidebar-ia.spec.ts::test@6
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 818c17f824a546d96e0081593fab93ba4d26a360086d460b0387df43a679303e
status: current
---

# drawer contains Dashboard and Finder; excludes My Schedule and separate Finder entries

## Purpose

Verifies the Information Architecture (IA) of the mobile sidebar (drawer) for the member dashboard. It ensures that the navigation menu correctly displays the "Dashboard" and "Crew & Boat Finder" links while strictly excluding legacy or redundant entries like "My Schedule" or "Crew Finder." It also validates that navigating via the Finder link correctly handles client-side hydration and tab selection.

## Invariants

- **Viewport is mobile-first.** Uses a fixed viewport of 375x812 to trigger the drawer-only (mobile) UI pattern.
- **Auth state is fixed.** Uses `auth-states/member.json` to ensure the test runs as a standard member, not an admin.
- **Navigation via Finder must land on the correct tab.** The test asserts that the URL contains the expected query parameters and that the Radix `tab` component has `aria-selected="true"`.
- **Legacy URLs must redirect.** The `/members/crewfinder` and `/members/boatfinder` paths must redirect to the unified `/members/finder` endpoint with the appropriate `tab` query parameter.

## Gotchas

- **Hydration delay.** Per commit `69f60cc`, the test must explicitly wait for the `tablist` to become visible and for the `aria-selected` attribute to be set. Navigating to the Finder page is not instantaneous; the test relies on client-side hydration to render the tabs.
- **Modal interference.** The mobile drawer is a `role="dialog"`. If the drawer is open, it must be dismissed (via `Escape` key) before the test can interact with the `tablist` or other page elements behind it.

## Cross-cutting concerns

- **Auth**: Uses `auth-states/member.json` (Member role).
- **Side effects**: Changes to the sidebar navigation structure will break this test, specifically regarding the visibility of "Dashboard" and "Crew & Boat Finder".

## External consumers

None known.
