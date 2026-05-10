---
node_id: concorda-test::tests/admin/system-settings.spec.ts::test@56
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 81219251839f914ec8ada557edd2b431af42eb96e38f6c9bc5a943f347f1c7ac
status: current
---

# payment config has mode selector

## Purpose

Verifies that the Payment Configuration section of the Admin System Settings page correctly displays the operational mode selector. This test ensures that users can distinguish between "test" and "live" modes via the UI, preventing accidental configuration changes in the wrong environment.

## Invariants

- **Requires `AdminSystemPage`** — The test relies on the `gotoPaymentConfig()` method to navigate to the correct sub-route.
- **Regex-based visibility** — The test validates the presence of mode-related text (e.g., "disabled", "test", "live") using case-insensitive regex to account for UI text variations.
- **Timeout sensitivity** — The selector for mode content expects a visibility timeout of 5,000ms, which is shorter than the 10,000ms used for the general configuration check.

## Gotchas

- **Initial scaffolding state** — Per commit `fd0c570`, this is part of the initial Playwright E2E suite scaffolding; the test is currently a baseline check and may not yet cover complex state transitions between modes.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session via `AdminSystemPage` to access the `/members/admin/payment` route.
- **Side effects**: Changes to the mode selector in this UI will affect the global Stripe configuration for the organization.

## External consumers

None known.
