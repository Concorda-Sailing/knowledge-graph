---
node_id: concorda-api::utils/email_utils.py::render_event_crew_request_to_owner_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1936429d2cc47d9b5ab8a7d0eb0123fa7e263561cb86f8969c214600db5aa727
status: llm_drafted
---

# render_event_crew_request_to_owner_email

## Purpose

Generates the HTML content for an email sent to a boat owner when a sailor requests to crew on their race. It constructs a specialized template that includes a "Review request" link or, if an `event_crew_id` is provided, direct "Accept" and "Decline" action buttons. Use this instead of generic event notifications when the intent is to facilitate a specific crewing decision-making flow.

## Invariants

- **Returns a `tuple[str, str]`** representing the subject and the HTML body.
- **`event_crew_id` determines the CTA type.** If present, the email includes direct links to `/api/invite/respond` via `_CrewRequestHandler`.
- **`base_url` is derived from `get_email_config(db)`**. This ensures the "Accept/Decline" buttons point to the correct environment-specific domain.
- **HTML escaping is mandatory.** All user-provided strings (`requester_name`, `event.name`, `boat_name`, `notes`) must be passed through `html.escape` to prevent injection in the email client.

## Gotchas

- **Direct-action links require authentication.** Per commit `8f96045`, the "Accept" and "Decline" buttons are designed to resolve through a specific API path, but the user will still be prompted to sign in before the response is recorded.
- **Timezone sensitivity.** Per commit `6c314f5`, ensure that any date strings passed into the template (via `_event_date_suffix`) are rendered in the organization's local timezone rather than UTC to avoid confusion for the boat owner.
- **The `boat_name` fallback.** If `sailing_event` is missing or the boat cannot be found, the function defaults to `"your boat"` to prevent empty or broken strings in the email body.

## Cross-cutting concerns

- **Auth**: Direct links in the email (Accept/Decline) resolve to `_CrewRequestHandler`, which requires a signed-in session.
- **Side effects**: Successful interaction with the links generated here updates the status of the `event_crew` record in the database.

## External consumers

None known.
