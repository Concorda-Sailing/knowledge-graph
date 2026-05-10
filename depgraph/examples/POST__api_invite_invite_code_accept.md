---
node_id: POST::/api/invite/{0}/accept
node_kind: endpoint
feature: crew-invites
last_reviewed: 2026-05-09
last_reviewed_against_hash: EXAMPLE_HASH_REGEN_TO_REPLACE_8c2fa1d4e09b
status: current
---

# POST /api/invite/{invite_code}/accept

## Purpose

Accept an outstanding crew invite. The invite token in the URL is a one-time secret that points either at:

- a `BoatCrew` row in `status="invited"` (existing-member path), or
- a `PendingCrewInvite` row (someone who didn't have an account when invited and has now signed up).

In either case, on success the user becomes an active crew member of the boat and the invite token is consumed. A websocket event (`boat_crew.updated`) tells every connected client to refetch the affected boat.

The route is mounted under `/api/invite/` (see `main.py`) — the matching `GET /api/invite/{code}` is the unauthenticated lookup that the email link first hits to render the landing page.

## Invariants

- **Invite tokens are stored only as SHA-256 hashes.** The raw token from the URL is hashed via `hashlib.sha256(token.encode()).hexdigest()` before any DB lookup. The raw token never lives in the database.
- **Email matching is normalized.** When a `pending` invite is being claimed, the logged-in user's email and the stored invite email are both passed through `_normalize_email` (Unicode NFC + strip + lowercase) before comparison. This is load-bearing: real emails differ in case and whitespace across systems.
- **Acceptance and token consumption happen in the same transaction.** A `BoatCrew` row is created (or updated) and the `PendingCrewInvite` row is deleted in a single `db.commit()`. A partial state where the invite is still claimable but the user is already on crew should never persist.
- **Already-on-crew is idempotent, not an error.** If the logged-in user is already in `BoatCrew` for this boat, the pending invite is deleted and the response is `{"message": "Already on crew", "boat_uuid": ...}`. This avoids a footgun where a duplicate accept (double-click, replay) returns a 409 the user can't recover from.
- **Expired and revoked invites must 404, not 410.** `_lookup_invite` filters `revoked_at IS NULL` and `expires_at >= now`. From the client's perspective, an expired invite is indistinguishable from a never-valid invite — we deliberately do not leak that the token was once real.

## Gotchas

- `record.status = "active"; record.invite_token = None` for the existing-member path is the correct shape — it converts the row in place. Re-using the row preserves the original `invited_by_uuid` and `notes`. Don't be tempted to delete-and-recreate; the audit trail depends on the existing row.
- The 403 returned for the existing-member path (`This invite is for a different user`) is a real auth check. If the wrong logged-in user clicks the link, we don't want to silently swap them in.
- This handler returns an **inline dict**, not a Pydantic model. That's the reason for the `weakly_typed_response` warning on the node. Adding a response_model would let the structural hash detect future shape changes; until then, manual review is required.

## Cross-cutting concerns

- **Auth:** Requires a valid bearer token. Public lookup uses the sibling `GET /api/invite/{code}` (no auth).
- **Websocket:** Emits `boat_crew.updated` on success. Consumers refetch via `/api/boats/{id}/crew`.
- **Rate limiting:** None specifically; relies on the global authenticated rate limiter. Consider tightening if invite-token brute-force becomes a concern (the tokens are 32-byte URL-safe so this is unlikely).
- **Audit:** No explicit audit log entry today. The websocket broadcast is the only signal. If we add an audit table, this is a write site.

## External consumers

- **Concorda iOS app** — accepts invites via deep link → in-app login → POST. Older shipped TestFlight builds can't be auto-updated. Response shape (`{message, boat_uuid}`) is part of the de-facto API contract for those builds. **Do not rename `boat_uuid` without coordinating an Expo release first.**

## Open questions

- Should we add a Pydantic `response_model` so the structural hash detects future response changes? The current inline-dict shape is the only reason this endpoint can drift silently across the HTTP boundary.
- Should expired-invite responses include a "request a new invite" hint in the body? Currently a flat 404; UX could be friendlier without leaking lifetime info.
