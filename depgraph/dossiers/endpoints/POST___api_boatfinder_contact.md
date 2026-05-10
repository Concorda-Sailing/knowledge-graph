---
node_id: POST::/api/boatfinder/contact
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ab9ad63d6ba6eaabd1cb793ebe260e7b959a61a5282b84b60c710a2e234af367
status: current
---

# POST /api/boatfinder/contact

## Purpose

Facilitates a proxy-email contact flow between a user and a boat owner. When a user expresses interest in a boat via the Boat Finder, this endpoint gathers the sender's profile details (name, phone, and sailing resume link) and sends an email to the owner. This allows users to initiate contact without exposing the owner's direct email address to the public web.

## Invariants

- **Requires `boatfinder.contact` permission** via the `require_permission` dependency.
- **Input must be a `BoatFinderContactRequest`** containing a `target_id` (the boat) and a `message`.
- **The `message` field is constrained** to a minimum length of 1 and a maximum of 2000 characters.
- **Returns a 404 error** if the `target_id` does not correspond to an existing boat.
- **Returns a 400 error** if the boat exists but its `BoatResume.published` status is `False`.
- **Returns a 400 error** if the `current_user` is the same as the boat owner (prevents self-contact).

## Gotchas

- **Rate limiting is enforced via `_check_rate_limit(sender.id)`**. This is a per-user throttle to prevent spamming boat owners.
- **Profile visibility is conditional.** If the sender has a `SailingResume` entry in the database, the email includes a `profile_url` and `profile_label` pointing to `/members/crewfinder`. If no resume exists, these fields are empty strings.
- **The `base_url` is dynamic.** The endpoint fetches `web_base_url` from the global `email_config` to construct the profile link; if this is misconfigured, the "View Resume" link in the email will be broken.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `boatfinder.contact` permission.
- **Rate limit**: Uses `_check_rate_limit` keyed by `sender.id`.
- **Audit**: Logs the transaction via `logger.info` with the pattern `"Boatfinder contact: {sender_id} -> {recipient_id} (boat/{target_id})"`.
- **Side effects**: Triggers an outbound email via `send_crewfinder_contact_email`.

## External consumers

- Web frontend (Boat Finder contact form).

## Open questions

- The `BoatFinderApplyRequest` (lines 272-275) is defined in the same file but is not yet used by a router-level function in the provided snippet; it is unclear if `/apply` is intended to be a separate, more restricted action than `/contact`.
