---
node_id: concorda-api::models/pending_crew_invite.py::PendingCrewInvite
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 52005eb7ae0ff12282fbfd88368419e9f250bbaf7d3ca4e70f0aa57258667904
status: current
---

# PendingCrewInvite

## Purpose

Backend model for crew invites sent to email addresses where the recipient doesn't yet have a `Person` row — i.e., a boat owner wants to invite someone who isn't in the system at all. Stores the invitee's email, the inviting boat, the inviter's UUID, an optional note, and a sha256-hashed `invite_token` whose raw form is mailed in the link. When the recipient clicks the email link and signs up (or logs in with the matching email), `routers/auth.py:763` and `routers/invite.py:99` convert this row into a real `BoatCrew` (status=`active`) and delete the pending row. Distinct from `BoatCrew`, which always has a real `person_uuid` (covers existing-member invites and accepted crew); distinct from `BoatShareInvite`, which is a person-less single-use share link rather than an email-targeted crew invite. Five dependents: the polymorphic remove/resend endpoints (`DELETE /api/boats/{0}/crew/{1}` and `POST .../resend-invite`, which dispatch on id and fall back to this table after `BoatCrew` misses), the owner-side list (`GET /api/boats/{0}/pending-invites`), the My-Crew aggregator (`GET /api/profile/crew`), and the batch-invite creator (`POST /api/boats/{0}/crew/invite-batch`).

## Invariants

- `invite_token` stored hashed (`sha256(raw)`); raw token only exists in the outgoing email. Lookups (`routers/invite.py:53`) re-hash the URL token before querying. Never store or log the raw token.
- `(boat_uuid, email)` unique — a single email can't have two pending invites for the same boat. Batch invite (`boats.py:676`) enforces this by skip-on-duplicate; do not bypass.
- `expires_at` and `revoked_at` are the security gate added in `8971b1c` (Tier-B). Lookup paths (auth signup, `/api/invite/{code}`) MUST filter out revoked rows AND treat past `expires_at` as 404. Without this, a leaked/archived link could be replayed after cancellation or after the 14-day window. TTL constant lives in `routers/boats.py:39` (`PENDING_INVITE_TTL_DAYS = 14`).
- Email comparisons use `func.lower(...)` on read (`auth.py:764`, `boats.py:678`) and signup uses NFC+strip+lowercase (`invite.py:_normalize_email`). Stored email is whatever the inviter typed; do not rely on stored casing.
- Conversion to `BoatCrew` is destructive — once accepted, the `PendingCrewInvite` row is `db.delete(...)`'d in the same transaction. There is no archival tombstone.
- `type="PendingCrewInvite"` is set in `__init__`; the model uses `BaseModel`'s STI/discriminator pattern. Don't override `type` from kwargs.

## Gotchas

- **Resend revives revoked rows.** `boats.py:521-530` clears `revoked_at` and resets `expires_at` on resend — an owner who cancels then re-invites the same email reuses the same row (fresh token, fresh window) rather than creating a new one. Audit/history is therefore lost.
- **Polymorphic `crew_id` slot.** Both `DELETE /api/boats/{boat_id}/crew/{crew_id}` and `.../resend-invite` first try `BoatCrew.id`, then fall back to `PendingCrewInvite.id`. A typo'd id silently 404s rather than 400-ing on type mismatch — see open question in the `boatApi.removeCrew` and `boatApi.resendInvite` dossiers.
- **Auth-signup auto-accept silently swallows pending invites by email match.** `auth.py:763` loops every non-revoked, non-expired pending row matching the registrant's email and deletes them while creating BoatCrew rows. If product later wants email verification before crew acceptance, this path is the bypass to close (memory `project_free_signup_verification` is the precedent for that pattern).
- **`datetime.utcnow()` is used directly** (boats.py:529, 693; auth.py:762; invite.py:52) — naive, not the project's `UtcDateTime` helper convention. Pre-existing pattern; flag if touching, especially since stored `expires_at`/`revoked_at` are naive `DateTime`. Comparisons currently work because all writes and reads go through `datetime.utcnow()`, but mixing in tz-aware values would silently break expiry filtering.
- **No `organization_id`.** Pending invites are boat-scoped, not org-scoped. If Tier-C scoping ever wants to constrain cross-org invites, this model has no hook for it.
- **No FK constraints** on `boat_uuid` or `invited_by_uuid`. Deleting a boat or inviter Person leaves orphan pending rows; nothing in the codebase cleans them up.

## Cross-cutting concerns

- **Auth:** owner-only on every mutation path (`_require_owner` in boats.py); the `GET /api/invite/{code}` lookup is intentionally unauthenticated so the email link works for anyone, but it returns no token material.
- **Email:** `send_boat_crew_invitation_email` is called post-commit with raw token; failures are swallowed (`try/except: pass`) — a row can exist with no email ever delivered. Toast/UX cannot distinguish "sent" from "DB-only".
- **Realtime:** all create/delete/resend paths broadcast `BOAT_CREW_UPDATED` scoped to `boat_id`. `BoatCrewTable` and `MyCrewTab` re-fetch.
- **Side effects on accept:** signup flow (`auth.py`) and `/api/invite/{code}/accept` (`invite.py:99`) both delete the pending row and create `BoatCrew(status="active")`. The accept paths are intentionally redundant — signup-by-email auto-accepts; explicit click-through accept covers users who already have an account at the target email.
- **Security audits:** `8971b1c` (Tier-B) added expiry/revocation; `c9a7c41` (Tier-A/B IDOR) tightened authz on the surrounding boat-crew endpoints. Don't loosen either without re-checking those audits.

## External consumers

None known. Email recipients (humans) are the only "external" consumer; no scheduled job sweeps expired rows (they just stop being valid on read), no webhooks fire, no mobile/Expo surface invokes the owner-side endpoints yet.

## Open questions

- Should expired/revoked rows be reaped by a scheduled job, or kept indefinitely as a soft history? Currently they accumulate and are only filtered at read time.
- Should accept-by-signup require email verification first (per `project_free_signup_verification` pattern), or is owner-issued invite trust sufficient to skip that gate?
- Should the polymorphic `crew_id` overload be split into separate `pending-invite` endpoints to clear up telemetry and 400-vs-404 semantics? Same question raised in the `removeCrew`/`resendInvite` dossiers.
- Should resend create a new row instead of reviving the revoked one, so cancellation history is preserved?
