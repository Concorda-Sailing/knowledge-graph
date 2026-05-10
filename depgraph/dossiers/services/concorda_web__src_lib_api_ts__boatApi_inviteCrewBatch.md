---
node_id: concorda-web::src/lib/api.ts::boatApi.inviteCrewBatch
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 498cf8e1df54593868c4042be317ffd229d6b0d13dd890d2fdf4dcce6afce599
status: llm_drafted
---

# boatApi.inviteCrewBatch

## Purpose

The `inviteCrewBatch` method handles bulk invitations to boat crew members via email addresses. It is used when an administrator or owner needs to invite multiple people simultaneously rather than using the single-member `inviteCrew` method.

## Invariants

- **HTTP Method is `POST`** — It sends a payload to `/api/boats/${boatId}/crew/invite-batch`.
- **Input structure is strict** — Requires a `boatId` and a `data` object containing an array of `emails` and an optional `notes` string.
- **Returns a summary object** — The response shape is `{ invited: number; skipped: number; errors: string[] }`.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to execute.

## Gotchas

- **Email-only vs. UUID** — Unlike `inviteCrew` which can take a `person_uuid`, this method is strictly for email-based batching.
- **Error handling is explicit** — The `errors` array in the response contains specific failure reasons (e.g., invalid email format or existing membership) that must be surfaced to the user rather than just treating the whole call as a generic failure.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`; requires valid user session.
- **Side effects**: Triggers the crew invitation flow which may impact the "accepting-crew" status visibility on regatta detail pages (per commit `2d6b8a7`).

## External consumers

- `concorda-web::src/components/boat/boat-crew-invite.tsx` (via `BoatCrewInvite` component).
