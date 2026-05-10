---
node_id: concorda-web::src/lib/api.ts::inviteApi.getInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9095d7fed84fed8aba7b9a89cf33770ca983df4baeea83f995d0ff6a774137e8
status: llm_drafted
---

# inviteApi.getInvite

## Purpose

Fetches the details of a specific invitation using a unique token. This is the entry point for the invitation-to-onboarding flow, providing the necessary context (user role, email, and boat association) to determine if a user is joining as a "crew" member or a "pending" invitee. It is distinct from `acceptInvite`, which is the subsequent mutation used to finalize the acceptance.

## Invariants

- **Returns `InviteDetails`** — the response includes `invited_by_name`, `role`, `invite_type`, and `has_account`.
- **Uses a single-path token** — the `token` parameter is the unique identifier for the specific invitation instance.
- **Unauthenticated access** — unlike `acceptInvite`, this method uses `fetchApi` (not `fetchApiAuthenticated`), allowing unauthenticated users to view the invitation landing page before signing in or registering.

## Gotchas

- **Role-based access requirements** — per commit `47688ac`, accepting a "co-owner" invite now requires the user to have a `Boat Owner` membership. If this method returns a role that requires higher privileges, the UI must handle the subsequent failure in `acceptInvite`.
- **Identity-driven UI state** — per commit `b67d359`, the UI relies on the data from this call to drive the "Accepting-Crew" badge visibility on regatta detail pages.
- **Registration vs. Login flow** — the `email` field in the response is used to determine if the user should be routed to a "Sign In" flow (if `has_account: true`) or a "Register" flow (if `has_account: false`).

## Cross-cutting concerns

- **Auth**: None (this is a public lookup via token).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: The data returned here drives the visibility of the "Accepting-Crew" badge on the regatta detail page and the schedule card.

## External consumers

- `concorda-web::src/app/invite/[token]/page.tsx` (InvitePageContent)
- `concorda-web::src/app/join/register/page.tsx` (RegisterPageContent)
