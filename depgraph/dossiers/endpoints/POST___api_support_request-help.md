---
node_id: POST::/api/support/request-help
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7b3599230dddad9c3b3371886614007c3dce784ec2a313eb1feac32d073d7302
status: current
---

# POST /api/support/request-help

## Purpose

Allows authenticated members to send a help request directly to the MBSA support inbox. This endpoint acts as a bridge between the web client and the support email system, packaging user identity (name, email, phone) with a custom message. It is distinct from standard event or organization-level communications, serving as a dedicated one-way contact channel.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Input schema** is defined by `RequestHelpRequest`, which must include a `message` string.
- **Returns a JSON object** `{"message": "Help request sent"}` upon successful execution.
- **Uses the user's identity** (name, email, phone) to populate the email metadata, ensuring the support team knows who is requesting help.

## Gotchas

- **Rate limiting is enforced via `_help_rate_limit`** using a sliding window. If a user exceeds the limit, the endpoint raises a 429 error.
- **The `sender_name` construction is sensitive to missing fields.** It uses a fallback logic: if both first and last names are empty, it defaults to the user's email address to ensure the support email has a valid display name.
- **Email delivery is a side effect of `send_support_request_email`.** If the email service provider is down, the endpoint may fail or hang depending on the implementation of the helper.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (authenticated user).
- **Rate limit**: Uses `_help_rate_limit` and `_check_rate_limit` to prevent spam.
- **Audit**: Logs the request via `logger.info("Support request: from=%s", sender.id)`.
- **Side effects**: Triggers an external email via `send_support_request_email`.

## External consumers

- `concorda-web::src/lib/api.ts::supportApi.requestHelp`
