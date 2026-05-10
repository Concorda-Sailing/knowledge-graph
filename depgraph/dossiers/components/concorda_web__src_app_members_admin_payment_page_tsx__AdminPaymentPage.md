---
node_id: concorda-web::src/app/members/admin/payment/page.tsx::AdminPaymentPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3d7e6148a0357dea63ec9179669bf5e99caa47d49e3a45ea03ed1ed7c6538ec8
status: llm_drafted
---

# AdminPaymentPage

## Purpose

Provides the administrative interface for configuring Stripe payment settings. It allows admins to toggle between "disabled" and active modes and manage the `stripe_publishable_key`, `stripe_secret_key`, and `stripe_webhook_secret`. This page is a specialized view within the admin settings ecosystem, distinct from general user or crew management.

## Invariants

- **Initial state is fetched via `adminPaymentConfigApi.get()`** — the component must wait for the loading state to resolve before allowing edits to prevent overwriting existing config with default empty strings.
- **`mode` is a strict union** — the `Select` component controls the `config.mode` value, which dictates whether Stripe processing is active.
- **Requires `admin.users.view` permission** — the `SettingsPage` wrapper enforces this permission check to ensure only authorized administrators can access or modify payment keys.
- **Updates are atomic via `adminPaymentConfigApi.update(config)`** — the entire `PaymentConfigData` object must be sent to the server to persist changes.

## Gotchas

- **UI/UX feedback loop** — the `saveSuccess` state is transient and uses a `setTimeout` of 3000ms to clear. If a user navigates away or the component unmounts during this window, the success state is lost, but this is handled by the local state.

## Cross-cutting concerns

- **Auth**: Requires `admin.users.view` permission via the `SettingsPage` component.
- **Side effects**: Changes to these keys directly affect the success/failure of the Stripe webhook listener and the ability of the frontend to initiate checkout sessions.

## External consumers

- None known.
