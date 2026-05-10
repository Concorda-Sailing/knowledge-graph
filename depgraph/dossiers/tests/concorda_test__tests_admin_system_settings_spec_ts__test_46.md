---
node_id: concorda-test::tests/admin/system-settings.spec.ts::test@46
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fd9abf1de30760063052e768078ddfed52bca9c9cd4f4683c44774e4aeb918b3
status: current
---

# payment config page loads

## Purpose

Verifies that the Payment Configuration page is accessible and correctly displays the Stripe integration status. It ensures the UI correctly surfaces the current payment mode (e.g., Test vs. Live) to the administrator. This test is distinct from the general `AdminSystemPage` setup as it specifically targets the routing and visibility of the payment-specific configuration sub-view.

## Invariants

- **URL Pattern**: The page must resolve to a path matching `/\/members\/admin\/payment/`.
- **Visibility**: The configuration content must contain specific keywords (`stripe`, `payment`, or `configuration`) to confirm the correct view is loaded.
- **Timeout**: Assertions on content visibility use a specific `10_000`ms timeout to account for potential loading-state delays in the admin dashboard.

## Gotchas

- **Initial scaffolding**: Per commit `fd0c570`, this test is part of the initial E2E suite scaffolding; it relies on the `AdminSystemPage` abstraction which may be in flux as the test suite matures.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (inherited from the `AdminSystemPage` context).
- **Side effects**: None.

## External consumers

None known.
