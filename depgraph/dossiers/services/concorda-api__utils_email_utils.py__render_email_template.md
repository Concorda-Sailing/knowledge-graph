---
node_id: concorda-api::utils/email_utils.py::render_email_template
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cb852036d55d6d8017c45469a4136e243757fbbbc2dbd64a8a7c3f59670e989a
status: llm_drafted
---

# render_email_template

## Purpose

Fetches a managed email template from the database and injects a set of variables into the subject and body. It is used to ensure that all user-facing emails follow a consistent structure and branding. It automatically injects `app_title` and `support_email` so callers don't have to manually provide them, though any caller-supplied variables will override these defaults in case of a collision.

## Invariants

- **Returns a `tuple[str, str]`** representing the (subject, html_body) pair.
- **Requires an active template.** If the template `name` does not exist or `is_active` is `False`, it raises a `ValueError`.
- **Automatic injection.** `app_title` and `support_email` are always present in the `enriched` dictionary used for substitution.
- **Variable precedence.** The `**variables` unpacking happens after the auto-injected keys, meaning caller-provided keys take precedence over defaults.

## Gotchas

- **Raising `ValueError` is intentional.** Per the docstring, the function is designed to raise an error if a template is missing or inactive so that the failure is captured in the `NotificationLog` rather than silently sending a broken or empty email.
- **Timezone-aware date rendering.** Per commit `6c314f5`, the helper `_format_event_date_for_email` must render dates in the organization's timezone (via `_to_org_local`) rather than UTC to avoid displaying incorrect event times to users.
- **Empty string fallbacks.** The helper `_format_event_date_for_email` returns an empty string `""` if the event or time is missing, allowing template logic like `{{event_date_suffix}}` to render cleanly without "None" or "Invalid Date" appearing in the email body.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: Failures in template fetching are intended to surface in the `NotificationLog`.
- **Rate limit**: None.
- **Side effects**: Used to prepare content for `event_crew.*` notifications via `notify_person`.

## External consumers

None known.
