---
node_id: concorda-api::utils/email_utils.py::render_event_crew_response_to_owner_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7ff3849fc6b0e3c206d462fcfd9f7b72eb28a7441e61b5d7e9ea1c1d42408027
status: current
---

# render_event_crew_response_to_owner_email

## Purpose

Generates the HTML email content sent to a boat owner when a crew member responds to a sailing event. It provides a high-level summary of the responder's status (accepted/declined) and includes a visual roster via `event_crew_status_block` so the owner can see the full context of the event's current lineup. Use this specifically for owner-facing notifications; for crew-facing notifications, use `render_event_crew_marked_response_email`.

## Invariants

- **Returns a `tuple[str, str]`** representing the rendered HTML body and the subject line (or metadata).
- **Requires a `db: Session`** to perform lookups for the `Boat` entity associated with the `sailing_event`.
- **Uses `html.escape`** on all user-provided strings (e.g., `owner.first_name`, `event.name`, `boat_name`) to prevent injection in the email body.
- **Relies on `render_email_template`** to inject the context into the `"crew_response_to_owner"` template.

## Gotchas

- **Timezone-aware rendering is critical.** Per commit `6c314f5`, the email body must render the event date in the organization's local timezone rather than UTC to avoid confusion for the boat owner.
- **Boat name fallback logic.** If the `sailing_event` or the associated `Boat` is missing, the function defaults to the string `"your boat"` to ensure the email remains readable and doesn't crash during string interpolation.
- **Template dependency.** This function is a consumer of the `"crew_response_to_owner"` template; changes to the template's expected keys (like `event_crew_status_block`) will break this renderer.

## Cross-cutting concerns

- **Auth**: None (generates content for an email, not a direct authenticated request).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers the delivery of a notification that updates the owner's awareness of crew changes.

## External consumers

None known.
