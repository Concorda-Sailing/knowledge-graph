---
node_id: POST::/api/boatfinder/apply
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0132126d61d0244cfa2232290236281f9034eaedfbc72b17413bee9e43a731c2
status: llm_drafted
---

# POST /api/boatfinder/apply

## Purpose

Allows a user to apply for a crew position on a specific boat. It triggers an email notification to the boat owner containing the applicant's profile details (or a placeholder if contact info is private) and creates a `BoatCrew` record with a "prospective" status. This is the primary mechanism for the "crew workflow" mentioned in recent updates.

## Invariants

- **Requires `boat_id` and `message`** (min 1, max 2000 chars).
- **Requires `boatfinder.contact` permission** via `require_permission`.
- **Must have an active `BoatResume`** where `published == True` for the target boat, otherwise returns 400.
- **Self-application is forbidden**: Returns 400 if `sender.id == recipient.id`.
- **Returns `{"message": "Message sent successfully"}`** on success.

## Gotchas

- **Rate limiting is enforced via `_check_rate_limit(sender.id)`**. If a user attempts to apply to multiple boats in rapid succession, this will trigger a failure.
- **Privacy-aware profile generation**: If `shares_contact` (derived from `crewfinder_prefs.get("opt_in")`) is false, the `profile_url` is stripped to prevent exposing the user's profile to the owner.
- **The `boat_name` fallback**: If `boat.name` is null, it falls back to `sail_number` or the string `"the boat"`. This is used in the email subject/body.

## Cross-cutting concerns

- **Auth**: Requires `require_permission("boatfinder.contact")`.
- **Rate limit**: Uses `_check_rate_limit` on the `sender.id`.
- **Side effects**: Triggers `send_crew_application_email`, which is the primary side effect for the crew workflow.

## External consumers

- `concorda-web::src/lib/api.ts::boatfinderApi.apply` (The primary web client consumer).
