---
node_id: concorda-test::tests/boats/mobile-boat-resume.spec.ts::goToFirstOwnedBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5862447b98e549b63f554533a35eba6b1bea4d01e0c6297c47095b1ea5dfd36c
status: llm_drafted
---

# goToFirstOwnedBoat

## Purpose

A navigation helper for mobile-specific Playwright tests. It navigates the browser to the `/members?tab=boats` route, selects the first available boat link, and waits for the boat-specific detail view to load. It is used to establish the starting state for "mobile boat resume" tests, ensuring the viewport is correctly set and the user is positioned on a specific boat's dashboard before testing tab-bar or hero-action visibility.

## Invariants

- **Navigation target**: Navigates to `/members?tab=boats`.
- **Locator strategy**: Selects the first `<a>` element where the `href` contains `boat=` or starts with `/members/boats/`.
- **Wait condition**: Waits for the "overview" tab to become visible with a 10s timeout to ensure the boat detail view is fully hydrated.
- **Viewport context**: Intended to be used within a 375x812 viewport context as defined in the `mobile boat resume` describe block.

## Gotchas

- **Default tab behavior**: The "overview" tab is the default active tab; clicking it is a no-op and can cause flakiness if the element is scrolled out of view. Tests should skip the click for the "overview" tab (see `a48c539` logic).
- **URL pattern matching**: Per commit `be406a9`, the locator must match both the legacy route and the new `?tab=boats` query parameter pattern to avoid broken navigation.
- **Scroll interference**: The sticky tab bar can overlap content; tests must call `window.scrollTo(0, 0)` before attempting to interact with tabs to ensure they are reachable.
- **Tab visibility**: The "profile" tab is no longer a top-level tab in the mobile view; it has been consolidated into the "overview" tab content (see `ba1c3bd`).

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (typically via `ApiClient.login`) to access the `/members` route.
- **Side effects**: Ensures the mobile "hero action" buttons (e.g., "Add Banner") are reachable and visible without hover interaction.

## External consumers

None known.
