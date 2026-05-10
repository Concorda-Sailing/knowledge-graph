---
node_id: concorda-api::utils/email_utils.py::render_event_crew_confirmed_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9573c0a300bfb20472dad1384c8ca7e69d1afe4cf1c4205b51b7313320f66c5c
status: current
---

# render_event_crew_confirmed_email

## Purpose

Generates the HTML email body for a crew member to notify them that a skipper has confirmed their position on a roster. This is a specialized renderer for the `crew_confirmed` template, distinct from the `render_event_crew_request_to_owner_email` sibling which handles the owner-facing side of the invitation flow. Use this when a user's status in an `event_crew` record has transitioned to confirmed.

## Invariants

- **Returns a `tuple[str, str]`** consisting of the rendered HTML body and the plain text/subject context.
- **Requires an active SQLAlchemy `Session`** (`db`) to resolve the `_event_portal_url`.
- **Uses `html.escape` on all dynamic strings** (first name, event name, boat name, and position) to prevent injection in the email body.
- **`dock_time_str` defaults to `"TBD"`** if the input is empty or null to ensure the UI doesn't show a blank space.
- **`position_suffix` is optional.** If `event_crew.position_name` is present, it is escaped and appended in parentheses to the email body.

## Gotchas

- **Timezone-aware rendering is critical.** Per commit `6c314f5`, the email body must ensure that any date/time-related strings (like `dock_time_str`) are rendered in the organization's timezone, not UTC, to avoid confusing the crew member.
- **Template dependency.** This function relies on the existence of the `"crew_confirmed"` template in the managed template system; changing the template name or required keys will break this call site.

## Cross-cutting concerns

- **Auth**: The `portal_url` generated here leads to a view that requires a signed-in session (as noted in the sibling `render_event_crew_request_to_owner_email` pattern).
- **Side effects**: Primarily used by the event/invite lifecycle to notify users of roster changes.

## External consumers

None known.
