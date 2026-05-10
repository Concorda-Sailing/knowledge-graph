---
node_id: concorda-api::utils/email_utils.py::render_event_crew_marked_response_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a3583c2c0d82cd4eb9dba377416011cf4f1a61bfb2b907b4ddc1c1c0a0dd389e
status: current
---

# render_event_crew_marked_response_email

## Purpose

Generates the HTML content and metadata for an email sent to a crew member when a skipper has marked a response on their behalf. This is a "soft prompt" notification, informing the user that their status has changed (e.g., from "pending" to "confirmed") via an action taken by the skipper. It is distinct from `render_event_crew_confirmed_email`, which is used for final roster confirmations rather than status updates.

## Invariants

- **Returns a tuple of `(html_body, plain_text_body)`** via the `render_email_template` helper.
- **Requires a `db` session** to perform lookups for the associated `Boat` and `event_portal_url`.
- **Uses `html.escape`** for `first_name`, `skipper_name`, `event_name`, and `boat_name` to prevent XSS in the rendered email body.
- **Provides a fallback for `boat_name`**; if the `sailing_event` or its associated boat is missing, it defaults to `"your boat"`.

## Gotchas

- **Timezone-aware rendering is mandatory.** Per commit `6c314f5`, the email body (specifically the `event_date_suffix`) must be rendered in the organization's timezone rather than UTC to ensure the user sees the correct local time for their event.
- **Template hardening required.** Per commit `8f84d2d`, all inputs passed to the template (like `status` and `event_name`) must be explicitly escaped via `html.escape` to ensure the renderer is hardened against malformed or malicious strings.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers user-facing notifications regarding event status changes.

## External consumers

None known.
