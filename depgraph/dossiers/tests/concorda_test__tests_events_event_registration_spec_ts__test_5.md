---
node_id: concorda-test::tests/events/event-registration.spec.ts::test@5
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 517a0ae2b4edfa4ce584ea9e1a8f9eb5ee545604138669af8cc6ba6b91a94bda
status: llm_drafted
---

# event detail page shows registration options

## Purpose

Verifies that the event detail page correctly displays registration UI elements, such as ticket types and quantity selectors, for specific events. It ensures that the `EventsPage` abstraction correctly interacts with the event detail view and that the registration flow (including quantity increments) is functional.

## Invariants

- **Requires `EventsPage` instance** — uses the `EventsPage` class to navigate to specific event slugs.
- **Relies on `networkidle`** — the quantity selector test (lines 26-39) requires waiting for the network to be idle to ensure the ticket data has loaded before interacting with the `+` button.
- **Uses regex-based text matching** — selectors for "register", "ticket", "skipper entry", and "crew entry" use case-insensitive regex to remain resilient to minor text changes.
- **Timeout defaults** — visibility assertions use a 10,000ms timeout, except for the crew ticket assertion which is explicitly set to 5,000ms.

## Gotchas

- **Initial scaffolding** — per commit `fd0c570`, this is part of the initial Playwright E2E suite scaffolding; the test suite is currently in a high-churn state as the E2E coverage is being built out.

## Cross-cutting concerns

- **Auth**: The `members-only event requires auth` test case (lines 41-49) implicitly relies on the existing authentication state of the test runner to determine if the "members-only" content is visible.
- **Side effects**: Successful interaction with the quantity selector (lines 26-39) is a precursor to the actual registration/checkout flow, though this specific test does not complete a purchase.

## External consumers

None known.
