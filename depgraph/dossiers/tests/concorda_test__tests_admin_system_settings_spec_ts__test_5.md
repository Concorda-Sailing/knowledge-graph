---
node_id: concorda-test::tests/admin/system-settings.spec.ts::test@5
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5a49c3532365e67bb95e52541e8d5714d4ba90e28fd0b1c016f77214556c01d1
status: llm_drafted
---

# system settings page loads

## Purpose

Verifies the core administrative configuration surfaces for the organization, specifically the System Settings and Payment Configuration pages. This test ensures that an administrator can access high-level identity (Organization Name) and financial configuration (Stripe mode) settings. It serves as a smoke test for the `AdminSystemPage` page object and the underlying routing for `/members/admin/system` and `/members/admin/payment`.

## Invariants

- **URL patterns must match** — the system settings must reside at `/members/admin/system` and payment config at `/members/admin/payment`.
- **Organization name visibility** — the `nameField` must be present and contain a non-empty value (defaulting to a fallback like 'MBSA' in the test) to pass the visibility check.
- **Page object dependency** — relies on `AdminSystemPage` to handle navigation and element selection.

## Gotchas

- **Manual Reversion** — the `can edit and save org name` test performs a destructive action (clearing and filling the name field) and must manually revert the value to the `original` state to prevent side effects on subsequent tests in the same runner.
- **Implicit Wait Requirement** — the `saveButton.click()` requires a `page.waitForTimeout(1000)` to allow the asynchronous state update to complete before the test proceeds to the reversion step.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session (likely via `api.login` or a pre-existing `storageState` as seen in the `ApiClient` pattern).
- **Audit**: Changing the organization name via the `saveButton` triggers an audit log entry in the backend.
- **Side effects**: Modifying the organization name affects the global identity of the organization across all user-facing views.

## External consumers

None known.
