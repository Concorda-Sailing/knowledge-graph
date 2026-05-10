---
node_id: concorda-api::utils/email_utils.py::send_crewfinder_contact_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 583d5966f66df5077497981971d00087ca5ec01b0f16a827d17fbeb9dce7d587
status: llm_drafted
---

# send_crewfinder_contact_email

## Purpose

Sends a proxy contact email when a user initiates contact via the Crewfinder interface. It wraps the sender's contact details (email, phone, or profile link) into an HTML template to protect the sender's direct identity while allowing the recipient to respond. This is distinct from `send_crew_application_email`, which is used for formal boat applications and includes more structured metadata like sailing experience.

## Invariants

- **Requires a valid `db: Session`** to render the template via `render_email_template`.
- **Input strings must be HTML-escaped.** The function uses `html.escape` on `sender_email`, `sender_name`, and `message` to prevent injection.
- **`contact_lines` construction is conditional.** If `sender_phone` or `profile_url` are empty, they are omitted from the HTML body to avoid rendering broken or empty links.
- **The `message` is converted to HTML.** Newlines in the raw message are replaced with `<br>` tags to ensure readability in the recipient's email client.

## Gotchas

- **Timezone consistency is critical for related flows.** Per commit `6c314f5`, ensure that any datetime data passed into email bodies (though not directly in this function) is rendered in the organization's timezone rather than UTC to avoid user confusion.
- **Template dependency.** This function relies on the `"crewfinder_contact"` template name; if the template is renamed or the schema of the context dictionary changes, the call will fail at runtime.

## Cross-cutting concerns

- **Auth**: None (called by API routes that handle authenticated/unauthenticated contact requests).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None explicitly defined here, but callers in `routers/crewfinder.py` and `routers/boatfinder.py` may be subject to broader API rate limits.
- **Side effects**: Triggers an outbound email via `send_email`.

## External consumers

- `POST /api/boatfinder/contact`
- `POST /api/crewfinder/contact`
