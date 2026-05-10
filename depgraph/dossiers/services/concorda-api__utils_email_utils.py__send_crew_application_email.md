---
node_id: concorda-api::utils/email_utils.py::send_crew_application_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 87ca6e1cd4cadac296569ca9f1f9103f0aae879d1c8e8074049bd2970a1b4823
status: llm_drafted
---

# send_crew_application_email

## Purpose

Constructs and sends a templated HTML email to a boat owner when a user applies for a crew position. It handles the conditional logic for displaying applicant contact details (email/phone) versus a system-generated `reply_url` based on the user's privacy settings. Use this instead of `send_email` when you need to inject specific sailing profile metadata like experience level, positions, or a truncated "about me" section.

## Invariants

- **Input is HTML-safe.** The function uses `html.escape` on all user-provided strings (name, message, boat name, etc.) to prevent injection.
- **`about_me` is truncated.** The `about_me` string is capped at 300 characters with an ellipsis to prevent excessively long email bodies.
- **`shares_contact` logic is binary.** If `True`, the email includes the `applicant_email` and `applicant_phone`; if `False`, it provides a `reply_url` for in-system communication.
- **Requires a `Session` object.** The `db` parameter is passed through to the underlying `send_email` call.

## Gotchas

- **Template dependency.** This function relies on the `"crew_application"` template name in `render_email_template`. If the template name is changed or the template is missing, the email will fail to render.
- **HTML formatting of `message`.** The `message` string is processed via `.replace("\n", "<br>")` to ensure line breaks are preserved in the HTML body.
- **Timezone rendering.** Per commit `6c314f5`, ensure that any time-based data passed into email templates is handled with the same timezone-aware logic used in the calendar system to avoid UTC-to-local discrepancies in the email body.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggered by `POST /api/boatfinder/apply`.

## External consumers

- `POST /api/boatfinder/apply` (via `routers/boatfinder.py:322`).
