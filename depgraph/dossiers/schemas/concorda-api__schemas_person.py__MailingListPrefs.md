---
node_id: concorda-api::schemas/person.py::MailingListPrefs
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8630e99f24cc2fc16f23a7d003b8ce1eefd944ddfae97a0a229ab3c0fd8b6d36
status: current
---

# MailingListPrefs

## Purpose

Defines the granular subscription settings for a person's communication preferences. It is a sub-component of the `Preferences` class within the `Person` schema, specifically isolating settings for automated email notifications. Use this to manage whether a user receives broad organizational updates versus specific event-driven notices.

## Invariants

- **`opt_in` is the master toggle.** If `opt_in` is `False`, the user is effectively unsubscribed from all automated communications managed via this schema.
- **`event_notices` defaults to `True`.** Unlike `opt_in`, this is enabled by default to ensure users receive critical updates regarding active events/regattas.
- **`general_news` defaults to `True`.** This controls non-critical organizational updates.
- **Strictly boolean fields.** All fields (`opt_in`, `event_notices`, `general_news`) must be boolean to satisfy the Pydantic model and prevent type errors in the API layer.

## Gotchas

- **Implicit dependency on `PersonRead`.** Because `MailingListPrefs` is nested within `Preferences`, which is itself a field in `PersonRead`, any change to the structure of this class propagates to the full person object returned by the API.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Changes to these flags may impact the logic of downstream email dispatchers (e.g., SendGrid integrations mentioned in commit `a7a8a37`).

## External consumers

None known.
