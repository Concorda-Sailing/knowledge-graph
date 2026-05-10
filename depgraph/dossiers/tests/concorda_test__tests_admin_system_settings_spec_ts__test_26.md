---
node_id: concorda-test::tests/admin/system-settings.spec.ts::test@26
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b2c1d5443653ec08efa62f93f6b246b8fee1f9e1b431f8c41f00964ca42e0589
status: llm_drafted
---

# can edit and save org name

## Purpose

Verifies the ability to modify the organization's name within the Admin System Settings. It ensures that the name field is editable, the save operation is successful, and the state can be reverted to the original value. This test is distinct from the payment configuration tests in the same file, which focus on routing and visibility of Stripe settings rather than form state mutation.

## Invariants

- **Requires `AdminSystemPage` instance** to interact with the organization name field and save button.
- **Uses a regex-based locator** (`/organization.*name|org.*name|name/i`) to find the input field, ensuring the test is resilient to minor label changes.
- **Expects a non-empty initial value**; the test fails if the organization name field is empty upon loading.
- **Reversion logic is mandatory**; the test must restore the `original` value to prevent polluting the test environment for subsequent runs.

## Gotchas

- **Hardcoded timeout dependency:** The test relies on `await page.waitForTimeout(1000)` after clicking the save button. This is a brittle way to wait for the API/UI to settle and could lead to race conditions if the network latency exceeds 1s.
- **Initial value fallback:** If `original` is null or undefined, the test defaults to `'MBSA'`. This assumes 'MBSA' is a valid/safe fallback for the test environment.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (likely via `AdminSystemPage` setup).
- **Side effects**: Mutates the organization name in the database, which may affect any UI elements displaying the organization name (e.g., headers or breadcrumbs) during the test run.

## External consumers

None known.
