---
node_id: POST::/api/crewfinder/contact
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 47afe7d6bceec9a63f5c8bb26d69476d156f483a6abc33c2c654cb819f8a35c9
status: llm_drafted
---

# POST /api/crewfinder/contact

## Purpose

Provides a proxy-based messaging system that allows users to contact crew members without exposing the recipient's direct email address. It gathers the sender's identity and boat-related context (like a published boat resume) to construct a professional email sent via `send_crewfinder_contact_email`. Use this endpoint when a user wants to initiate contact from a profile view while maintaining privacy-preserving boundaries.

## Invariants

- **Requires `crewfinder.contact` permission** via the `require_permission` guard.
- **POST request body** must conform to `CrewfinderContactRequest`.
- **Returns a 404** if the `target_id` does not match a valid `Person`.
- **Returns a 400** if the recipient has not opted into the `crewfinder` preference key or if the sender attempts to contact themselves.
- **Returns a 429** if the sender exceeds the rate limit defined by `_RATE_LIMIT_MAX`.

## Gotchas

- **Rate limiting is in-memory and per-sender.** The `_contact_rate_limit` list tracks timestamps for the `sender_id`. If the server restarts or the user's session context changes, the limit resets, but it is strictly enforced via `_check_rate_limit`.
- **PII/Privacy protection is critical.** Per commit `33a37a3`, this endpoint is a primary gatekeeper for preventing direct contact-based PII leaks. Do not modify the logic to return the recipient's email or direct contact info in the response.
- **Contextual profile links depend on `BoatResume`.** The `profile_url` and `profile_label` are only generated if the sender has a `BoatResume` where `published == True`. If this logic is broken, the email sent to the recipient will lack the professional context of the sender's boat.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `crewfinder.contact` permission.
- **Rate limit**: Uses `_contact_rate_limit` and `_RATE_LIMIT_MAX` to prevent spam.
- **Side effects**: Triggers an external email via `send_crewfinder_contact_email`.

## External consumers

- `concorda-web::src/lib/api.ts::crewfinderApi.contact`
