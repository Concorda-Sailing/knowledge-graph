---
node_id: concorda-web::src/app/members/admin/sms/page.tsx::SMSConfigPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ae10d6e250d6f1da8a3f2c6e6011b11fda1f2442f7ede9bca85d0272dae6e3d3
status: llm_drafted
---

# SMSConfigPage

## Purpose

Provides the administrative interface for configuring Twilio credentials and SMS/WhatsApp notification settings. It manages the state for Twilio SID, Auth Token, and phone numbers, providing a "Test SMS" utility to verify connectivity. This is a specialized view within the admin settings hierarchy, distinct from general notification settings as it handles sensitive credential injection.

## Invariants

- **Uses `adminNotificationConfigApi`** for all network operations.
- **Initial state fallback:** If the API call fails, the component defaults to a "safe" state with all credentials and phone numbers set to `null` or `"off"` to prevent UI crashes.
- **Permission requirement:** The `SettingsPage` wrapper requires `admin.users.view` permission to render the content.
- **Update payload:** The `update` method specifically targets `twilio_account_sid`, `twilio_auth_token`, `twilio_phone_number`, and `sms_enabled`.

## Gotchas

- **Mobile layout reflow:** Per commit `019f6e3`, the admin grid layouts (including this page) require a single-column reflow for mobile devices to prevent form elements from clipping or stacking incorrectly.
- **State synchronization:** The `handleSave` function performs a local state update (`setConfig`) after a successful API call to ensure the UI reflects the server-side truth without a full page reload.

## Cross-cutting concerns

- **Auth**: Requires `admin.users.view` permission via the `SettingsPage` component.
- **Side effects**: Updates to this configuration directly affect the reliability of SMS/WhatsApp notification delivery for the organization.

## External consumers

None known.
