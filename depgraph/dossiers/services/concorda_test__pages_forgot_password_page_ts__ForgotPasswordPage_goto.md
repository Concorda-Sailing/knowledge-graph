---
node_id: concorda-test::pages/forgot-password.page.ts::ForgotPasswordPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 310c1682a9d17ae016714c9b5a85bdadf334754847d01b1153dcfd71359b512b
status: current
---

# ForgotPasswordPage.goto

## Purpose

Navigates the Playwright browser to the `/forgot-password` route. This is the entry point for testing the password recovery flow, specifically for verifying that the system correctly handles email-based reset requests without leaking account existence via the UI.

## Invariants

- **Navigates to `/forgot-password`** — the absolute path is hardcoded to ensure the user is on the correct recovery page.
- **Uses regex-based selectors** — the `submitButton` and `successMessage` rely on case-insensitive regex (e.g., `/send|reset|submit/i`) to remain resilient to minor text changes in the UI.

## Gotchas

- **Initial scaffolding only** — per commit `fd0c570`, this file is part of the initial E2E suite scaffolding; it currently only contains the `goto` and `submitEmail` methods and lacks complex assertion logic for the recovery lifecycle.

## Cross-cutting concerns

- **Auth**: None. This page is accessed by unauthenticated users.
- **Side effects**: Successful execution of `submitEmail` triggers the backend password reset email flow.

## External consumers

None known.
