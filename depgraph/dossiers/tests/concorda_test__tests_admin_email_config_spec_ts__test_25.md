---
node_id: concorda-test::tests/admin/email-config.spec.ts::test@25
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ae69c2038b7c62ab23027cb9e3f03c4124ab18c70c02cfb1adbe0c30d108cd88
status: llm_drafted
---

# can navigate to email configuration

## Purpose

Verifies that the admin can successfully navigate to the email configuration sub-route and that the configuration UI (SMTP/SendGrid/Mode) is visible. This test ensures that the administrative interface for email settings is not only accessible but also renders the expected configuration controls and save buttons.

## Invariants

- **Requires navigation to `/members/admin/email`** to trigger the view.
- **Relies on `networkidle`** to ensure the configuration form is fully loaded before checking for visibility.
- **Uses regex-based text selection** (`/smtp|sendgrid|mode|configuration/i`) to identify the configuration section, allowing for slight variations in UI text.
- **Conditional assertion**: The test only asserts the visibility of the "Save" button if the configuration content is actually detected, preventing false negatives if the UI state is unexpected.

## Gotchas

- **Selector fragility**: Per commit `f552929`, selectors for the email settings section and configuration content must be carefully aligned with the actual UI text to avoid flaky failures.
- **Timing sensitivity**: The test uses a specific `3_000`ms timeout for the `saveButton` visibility check; if the API response for email settings is slow, this may fail under heavy load.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (inherited from the test file's setup/context).
- **Side effects**: Verifying this page ensures the admin can access the settings that control the global email delivery provider (SMTP vs SendGrid).

## External consumers

None known.
