---
node_id: concorda-api::utils/email_utils.py::send_boat_crew_invitation_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7d848f7b0e98d555fb3b7266cfa10faf409d621ae2d103476f502ac5523eb43f
status: current
---

# send_boat_crew_invitation_email

## Purpose

Sends an invitation email to a potential boat crew member. This function handles two distinct invitation flows: the "existing-member" flow (using `boat_crew_id` to provide Accept/Decline buttons) and the "pending-invite" flow (using `invite_token` to provide a registration link). Use this instead of generic event notifications when the intent is to add a person to a specific boat's crew.

## Invariants

- **`inviter_email` is the `Reply-To` address.** This allows recipients to reply directly to the boat owner via their mail client.
- **CTA logic is mutually exclusive.** If `boat_crew_id` is provided, the email renders Accept/Decline buttons; if omitted, it renders a single `invite_token` link.
- **HTML escaping is mandatory.** All user-provided strings (`first_name`, `boat_name`, `invited_by_name`, `notes`) must be escaped via `html.escape` to prevent injection in the email body.
- **`base_url` is derived from `get_email_config(db)`.** The link destinations (portal/accept/decline) are relative to this configured host.

## Gotchas

- **`Reply-To` implementation was a recent requirement.** Per commit `8c29970`, the `inviter_email` must be explicitly passed to ensure the recipient can contact the boat owner directly.
- **Two-step verification for existing members.** As noted in the docstring and reinforced by the `8c29970` pattern, if using `boat_crew_id`, the recipient must be signed in (or have a session) for the `/api/invite/respond` endpoint to verify their identity against the `person_uuid`.

## Cross-cutting concerns

- **Auth**: The `accept_url` and `decline_url` paths require an authenticated session to verify the user's identity against the `boat_crew_id` row.
- **Side effects**: Successful response to these emails triggers updates to the boat crew membership status in the database.

## External consumers

None known.
