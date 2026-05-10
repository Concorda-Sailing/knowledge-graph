---
node_id: concorda-test::pages/admin/system.page.ts::AdminSystemPage.gotoPaymentConfig
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0b792dae3d9e913142018f67719548997e73de176d0e9521272dc08138ab444d
status: current
---

# AdminSystemPage.gotoPaymentConfig

## Purpose

Navigates the Playwright browser instance to the Payment Configuration page. This is a specialized navigation helper within the `AdminSystemPage` class, used to isolate testing of payment gateway settings and billing configurations. It is distinct from `gotoEmailConfig` or `gotoSystem`, which target different administrative sub-sections.

## Invariants

- **Navigates to `/members/admin/payment`**.
- **Waits for `networkidle`** after the navigation to ensure the payment gateway configuration components and any external scripts have finished loading.
- **Requires an authenticated session** via the `AdminSystemPage` instance to access the route.

## Gotchas

- **Initial scaffolding only**: Per commit `fd0c570`, this file is part of the initial E2E suite scaffolding. The navigation patterns (specifically the `networkidle` wait) are currently being established and may need adjustment as the complexity of the payment configuration UI grows.

## Cross-cutting concerns

- **Auth**: Requires an admin-level session; navigation will fail or redirect if the user lacks permissions.
- **Side effects**: Navigating here triggers the loading of payment provider status indicators (e.g., Stripe/PayPal connection status).

## External consumers

- `concorda-test::tests/admin/system-settings.spec.ts` (used in setup hooks for testing billing configurations).
