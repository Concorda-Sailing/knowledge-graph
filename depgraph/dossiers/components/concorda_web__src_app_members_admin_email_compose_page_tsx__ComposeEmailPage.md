---
node_id: concorda-web::src/app/members/admin/email/compose/page.tsx::ComposeEmailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6d60b9bb3ed6650d8d18671e025b1d3147b142a8af4a1f870c11d661bda3d1d5
status: llm_drafted
---

# ComposeEmailPage

## Purpose

The administrative interface for composing and dispatching bulk emails to specific temporal product cohorts. It allows admins to either draft custom messages or select from pre-defined `EmailTemplate` objects. This page is used to communicate time-sensitive updates (like membership changes or product-specific announcements) to specific segments of the user base.

## Invariants

- **Template vs. Custom Mode:** If a template is selected, `subject` and `body` are omitted from the payload and `template_id` is sent instead. If no template is selected, `subject`, `body`, and `template_id` are sent.
- **Audience Requirement:** The `canSend` state requires at least one `product_id` or the `include_delegates` flag to be true, alongside non-empty subject/body fields.
- **Data Fetching:** On mount, the component fetches both `adminTemporalProductsApi.list` (filtered by current year and "Membership" category) and `adminEmailTemplatesApi.list`.
- **Template Filtering:** The `templates` state only stores items where `is_active` is true, ensuring admins don't accidentally send deprecated templates.

## Gotchas

- **Template State Reset:** When `handleTemplateChange` receives `"none"`, it explicitly clears the `subject` and `body` state. This prevents a user from selecting a template, typing a custom message, and then switching to "none" while accidentally retaining the custom text in the background.
- **Payload Ambiguity:** The `adminEmailConfigApi.sendBulk` call uses conditional logic to decide whether to send `subject`/`body` or `template_id`. If an agent modifies the `usingTemplate` logic, they must ensure the `undefined` fallback remains to satisfy the API's expected shape.

## Cross-cutting concerns

- **Auth**: Requires admin-level permissions to access `adminEmailConfigApi`.
- **Side effects**: Successful sends via this page impact the user-facing communication flow for members in the selected `TemporalProduct` categories.

## External consumers

None known.
