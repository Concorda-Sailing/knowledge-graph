---
node_id: concorda-api::utils/email_utils.py::send_crew_calendar_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f03a823733b94efd8dd049fd52b6055b3df42483736cbd8224fb358745b7a563
status: llm_drafted
---

# send_crew_calendar_email

## Purpose

Sends specialized, templated emails to boat crew members regarding event changes (invites, cancellations, or schedule updates). It handles the construction of complex context including localized time strings and dynamic URLs for accepting/declining invites. Use this instead of generic email helpers when the recipient is a crew member and the context involves a specific event/boat schedule.

## Invariants

- **Requires a valid `db` session** to fetch `OrgConfig` and `get_email_config`.
- **`kind` must be a member of `CREW_EMAIL_KINDS`** or it raises a `ValueError`.
- **`tz_id` defaults to `America/New_York`** if the organization's timezone is not explicitly set in `OrgConfig`.
- **`event_id` and `eventcrew_uuid` are required** to construct the `portal_url` and the `accept_url`/`decline_url`.
- **Returns `None`** (the function is a side-effect-driven service, not a data provider).

## Gotchas

- **Timezone rendering must be explicit.** Per commit `6c314f5`, the function must render the `.ics` attachment and the email body using the organization's timezone (via `tz_id`) rather than UTC to prevent confusing crew members about event start times.
- **URL construction is conditional on `kind`.** If `kind == "invite"`, the `accept_url` and `decline_url` are populated; for other kinds, these remain empty strings.
- **`boat_name` fallback logic.** If `boat_name` is passed as `None`, the function falls back to `boat_sail_number` to ensure the email body has a recognizable identifier.

## Cross-cutting concerns

- **Auth**: None (internal service call).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers email delivery for event-related lifecycle changes (e.g., when a crew member is added or an event is rescheduled).

## External consumers

None known.
