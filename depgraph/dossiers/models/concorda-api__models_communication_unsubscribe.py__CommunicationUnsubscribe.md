---
node_id: concorda-api::models/communication_unsubscribe.py::CommunicationUnsubscribe
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dee46e73d4491c9e4ac53ddde38f8c73ccb344c8f92e36d0a74e0764bd22e431
status: llm_drafted
---

# CommunicationUnsubscribe

## Purpose

Tracks user-initiated opt-outs for specific communication channels and topics. It serves as the source of truth for the notification engine to determine whether a message should be suppressed for a given `person_uuid` and `address`. This model is distinct from global user preferences, as it allows for granular unsubscribes (e.g., unsubscribing from a specific `topic` like "weekly_digest" while remaining subscribed to "emergency_alerts").

## Invariants

- **`person_uuid` is nullable** — Allows for "anonymous" unsubscribes (e.g., via a link in an email where the user isn't logged in).
- **`channel` is required** — Must specify the medium (e.g., "email", "sms", "push").
- **`address` is required and indexed** — The unique identifier for the channel (e.g., the actual email address or phone number).
- **`unsubscribed_at` is a mandatory DateTime** — Tracks the exact moment the opt-out occurred for audit and compliance.
- **`topic` defaults to `"all"`** — If no specific topic is provided, the unsubscribe applies to all communications for that address/channel.

## Gotchas

- **Schema redesign dependency** — Per commit `ee82e42`, this model is part of a recent structural shift in how relationships and data migrations are handled. Ensure any new fields added to the communication layer respect the new relationship table patterns established in this commit.

## Cross-cutting concerns

- **Auth**: None (typically used by unauthenticated email-link flows).
- **Websocket**: None.
- **Audit**: Y (records the `reason` and `source` for compliance auditing).
- **Rate limit**: None.
- **Side effects**: The notification engine must query this table before dispatching any outbound message to prevent sending suppressed content.

## External consumers

None known.
