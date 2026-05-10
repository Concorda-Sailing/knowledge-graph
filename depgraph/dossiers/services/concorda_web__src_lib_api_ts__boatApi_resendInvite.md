---
node_id: concorda-web::src/lib/api.ts::boatApi.resendInvite
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 75567aa44bffaa700d24a666dc40ca0764e770d418c69251d8e439b87983b07d
status: llm_drafted
---

# boatApi.resendInvite

## Purpose

Client-side mirror for resending a pending crew invite — renews the email link when the original has gone stale, expired, or the recipient lost it. Owner-side action targeting either a `BoatCrew` row with `status='invited'` (person already exists in the system) or a `PendingCrewInvite` row (invitee identified only by email, not yet a Person). The single endpoint `/api/boats/{boat_id}/crew/{crew_id}/resend-invite` polymorphically dispatches on the id — backend tries `BoatCrew` first, falls back to `PendingCrewInvite`. Three components consume it: `BoatCrewTable` (boat detail page, owner view) and `MyCrewTab` (twice — once for each invite kind via `handleResendInvite` / `handleResendPendingInvite`).

## Invariants

- Owner-only: backend gate is `_require_owner(db, boat_id, current_user.id)`. Non-owners get 403.
- For `BoatCrew` path, `status` MUST be `"invited"` — any other status returns 400 ("Invite is not in pending state"). Don't let UI offer the action for accepted/declined rows.
- Resending rotates `invite_token` (new `secrets.token_urlsafe(32)`, sha256-hashed at rest, raw token in email). The old link is invalidated.
- `BoatCrew.created` is reset to `utcnow()`; `PendingCrewInvite` resets `modified`, extends `expires_at` by `PENDING_INVITE_TTL_DAYS`, and clears `revoked_at`. Resending revives a revoked pending invite.
- Both paths broadcast `BOAT_CREW_UPDATED` over the websocket so other owner sessions refresh.
- The single `crewId` parameter is overloaded — it can be either a `BoatCrew.id` or a `PendingCrewInvite.id`. Callers must pass whichever id matches the row they're rendering.

## Gotchas

- Email-send failure is silently swallowed (`try/except: pass` on both branches). The endpoint returns `{"message": "Invite resent"}` even if SMTP failed — UI cannot distinguish "email actually sent" from "DB updated, email lost". Treat the toast as "we tried", not "delivered".
- `datetime.utcnow()` is used directly rather than the project's `UtcDateTime` helper convention (see memory: "Datetime storage = UTC-aware via UtcDateTime"). Pre-existing pattern in this file; flag if touching.
- `MyCrewTab` calls this twice with separate handlers — the *only* difference is the toast UX and which id is passed. Easy to drift; if behavior diverges (e.g., different optimistic UI for pending vs. invited), the duplication will hide it.
- No rate limit / throttle on the endpoint. Nothing stops an owner from spamming the resend button; recipient gets one email per click.
- `inviter_email` is passed for Reply-To threading; if the inviter Person row is missing it falls through to `None` rather than failing.

## Cross-cutting concerns

- **Auth**: `require_auth` + `_require_owner`. Tier-C scoping not relevant (boat-scoped, not org-scoped).
- **Websocket**: emits `BOAT_CREW_UPDATED` on the boat channel — `BoatCrewTable` and `MyCrewTab` subscribers will refetch.
- **Email**: `send_boat_crew_invitation_email` with raw (un-hashed) token in the link; `boat_crew_id` only set on the `BoatCrew` branch (pending branch passes None).
- **Token rotation**: any in-flight click on the old email link will 404/401 after a resend. Acceptable, but worth knowing for support tickets.
- **Audit**: no audit-log entry is written. Resends are invisible in history.

## External consumers

None known. No mobile app call site, no scheduled jobs, no webhooks. Expo iOS app does not yet expose owner-side crew management.

## Open questions

- Should resend be rate-limited per (boat, crew_id) — e.g., one resend per N minutes — to prevent accidental email spam? Currently nothing guards it.
- Should the email-send failure surface to the caller (HTTP 502 or a flag in the response) so the UI can warn? Current swallow is friendly but misleading.
- Should this be split into two endpoints (`/crew/{id}/resend` vs `/pending-invite/{id}/resend`) instead of overloading on id? The polymorphic dispatch is cute but means a typo'd id silently 404s rather than 400-ing on type mismatch.
