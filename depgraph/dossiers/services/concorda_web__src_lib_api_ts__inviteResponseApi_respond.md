---
node_id: concorda-web::src/lib/api.ts::inviteResponseApi.respond
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d399356d92186b3a1fbbd0da48d0da7396d2d250ea6b1e5051c59af9d6a9ae5e
status: llm_drafted
---

# inviteResponseApi.respond

## Purpose

Submits a user's decision (accept or decline) regarding a specific invitation. It acts as the client-side trigger for the `services/invite_dispatch` backend handler. Use this instead of generic approval APIs when handling the specific "accept/decline" flow for sailing-event crew slots or co-owner invitations.

## Invariants

- **Method is `POST`** to `/api/invite/respond`.
- **Requires an `id` (string)** representing the unique identifier for the invitation.
- **Requires a `decision`** which must be exactly `"accepted"` or `"declined"`.
- **Returns `InviteRespondResult`**, which contains a `kind` (string), a `status` (`"recorded"` or `"already"`), and an optional `detail` string.

## Gotchas

- **Backend handler dependency:** This method is a thin wrapper around the `services/invite_dispatch` backend handler.
- **Status ambiguity:** The `status` field in the response can be `"already"`, indicating the user has already responded to this invitation.
- **Role-based requirements:** Per commit `47688ac`, accepting a co-owner invite may require specific membership status (Boat Owner) to be valid in the broader business logic.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user is logged in and authorized to respond to the invite.
- **Side effects**: Successful responses trigger updates to the "accepting-crew" status and may affect the "schedule-card" count/display (per commit `b4d60c6`).

## External consumers

- `InviteResponsePage` in `src/app/members/invite/[action]/[id]/page.tsx`.
