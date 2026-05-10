---
node_id: concorda-test::tests/events/event-registration.spec.ts::test@41
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 633ea35e112950caeb00c3edc18ec88fbee888719ede232115bba88971c993c1
status: current
---

# members-only event requires auth

## Purpose

Verifies that the "Fall Regatta 2026" event page correctly enforces membership restrictions. It ensures that the page either displays the event content or a clear "members-only" indicator, confirming that the UI handles restricted access-control states gracefully.

## Invariants

- **Requires authentication/membership** — The test assumes the user context is already established (either via a previous test step or a global setup) to verify the transition from unauthenticated to restricted view.
- **Regex-based assertion** — The test expects the presence of either the string "fall regatta" or "members only" (case-insensitive) to pass.
- **Network-idle dependency** — Relies on `page.waitForLoadState('networkidle')` to ensure the event details and access-control banners are fully rendered before assertion.

## Gotchas

- **Initial commit scaffolding** — Per commit `fd0c570`, this is part of the initial Playwright E2E suite scaffolding; the test may be brittle if the underlying event-routing or membership-guard logic is refactored.

## Cross-cutting concerns

- **Auth**: Depends on the authenticated state of the current Playwright context to determine if the "members-only" view is triggered.
- **Side effects**: Affects the visibility of the event-detail view for the `fall-regatta-2026` slug.

## External consumers

None known.
