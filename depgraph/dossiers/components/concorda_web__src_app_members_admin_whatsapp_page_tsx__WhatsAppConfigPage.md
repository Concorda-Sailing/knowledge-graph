---
node_id: concorda-web::src/app/members/admin/whatsapp/page.tsx::WhatsAppConfigPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 91e7e1df2b86c7a7010326b815a8c6882dc2a3cd6ccba043cc1757d09378ca92
status: current
---

# WhatsAppConfigPage

## Purpose

Provides the administrative interface for configuring WhatsApp messaging via Twilio. It allows admins to set the WhatsApp phone number, toggle the service on/off, and trigger a test message to a specific phone number to verify connectivity. This is distinct from the general `adminNotificationConfigApi` usage as it focuses specifically on the WhatsApp-specific fields and the `testWhatsApp` action.

## Invariants

- **Requires `admin.users.view` permission** via the `SettingsPage` wrapper.
- **Initial state fallback:** If the API call fails, the component initializes with a null-state config (all Twilio/WhatsApp fields set to `null` or `"off"`) to prevent a hard crash.
- **Update payload is partial:** The `handleSave` function only sends `whatsapp_phone_number` and `whatsapp_enabled` to the `adminNotificationConfigApi.update` method.
- **Test functionality requires `testPhone`:** The `handleTest` function will return early if the input string is empty.

## Gotchas

- **Mobile broadcast issues:** Per commit `f8b1bc2`, there is a known issue with broadcast/config composer action clusters stacking on small screens; ensure any UI changes to this page do not exacerbate layout stacking issues on mobile views.

## Cross-cutting concerns

- **Auth**: Requires `admin.users.view` permission.
- **Side effects**: Updating the configuration via `adminNotificationConfigApi.update` affects the global notification state, which may impact how automated messages are routed in the backend.

## External consumers

None known.
