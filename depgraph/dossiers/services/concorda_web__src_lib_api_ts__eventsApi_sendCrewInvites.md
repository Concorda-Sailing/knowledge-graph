---
node_id: concorda-web::src/lib/api.ts::eventsApi.sendCrewInvites
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ef61b56aaccd17d0b3d25e7e3f4dfcb122734b94044d60427890304724d9475b
status: llm_drafted
---

# eventsApi.sendCrewInvites

## Purpose

Client-side mirror for the boat owner sending crew invites — `POST /api/events/{event_id}/sailing-event/crew-invite`. This is the partner of `respondToEventCrew`: where the owner pushes invites out, that endpoint is how recipients answer. Two modes: with `personUuids` it's a *targeted* invite (creates pool rows on the fly if missing, flips existing pool/declined/requested rows to `invited`); with `personUuids` omitted/null it's the *bulk* legacy path that transitions every `status="pool"` row at once. Returns the full refreshed roster (`EventCrewMember[]`), not just the affected rows, because each invite triggers an email + websocket fanout and callers need the post-state to render. The owner inviting themselves is auto-`accepted` (no decision to make); co-owners get real `invited` rows so they can decline if double-booked. 3 components consume: `event-crew-card.tsx` (×2 — accept-pool button and per-person targeted invite) and `event-plan-panel.tsx`.

## Invariants

- **Owner-only.** Handler is scoped `relation="owner"`; crew/co-owners cannot invite. Don't expose this in non-owner UI surfaces.
- **Status writes are `INVITED` for everyone *except* the inviter themselves**, who is auto-set `ACCEPTED` (rule `event_crew::status_enum` — both are valid sink states). Don't downgrade `accepted` or `confirmed` rows; the handler explicitly skips them in the targeted path.
- **Pool ordering = priority order.** Per `project_invite_priority_order`, the `personUuids` array is in click order = priority 1, 2, 3… The bulk path inherits whatever order rows were inserted into the pool. UIs that build the array must not re-sort it (alphabetical, by name, by status) before sending — that destroys the priority signal that future cap policies rank from.
- **`invited_by_uuid` = `current_user.id`** is set on every transitioned row; it's the audit trail for "who pushed the invite."
- **Returns the full roster** for the sailing event after commit — callers can render directly without a follow-up `getEventCrew` round-trip.

## Gotchas

- **Co-owner auto-accept silently bit us before the `_set_invite_status` split.** Self-invites auto-accept (no decision); everyone else, including co-owners on the same boat, must get a real `invited` row so they can decline if double-booked. Don't "optimize" by auto-accepting anyone whose person_uuid is in the boat's owner set — that's the regression the current code reverses.
- **The bulk path (`personUuids` null) only catches `status="pool"` rows.** Declined/requested rows are *not* re-invited by bulk; only the targeted path can pull those forward. UI that exposes a "send all invites" button after some declines must use the targeted path with explicit uuids, or those rows stay stuck.
- **Targeted invite creates missing rows on the fly** at `status="pool"` then immediately transitions them — so calling with a uuid that's never been in the pool *will* invite them. This is intentional (the priority click flow lets owners invite people who weren't pre-pooled) but it means the client doesn't have to call `setCrewPool` first.
- **No hard-cap or soft-cap enforcement here.** This endpoint will happily over-invite past `positions_needed` slot counts; cap policy lives in `evaluate_roster` at *response* time (alternate vs main) and in the response handler's per-position open-slot check. Owner UIs have to surface "you've invited more than slots" warnings client-side — the API won't 400.
- **No idempotency / dedup on rapid double-clicks.** A second targeted invite for the same uuid re-fires the email + websocket. Disable the button on first click; don't rely on server suppression.

## Cross-cutting concerns

- **Email**: every transitioned-to-`invited` row triggers either the assigned-position SMS/WhatsApp or the open-position invite, plus an HTML email + `.ics` calendar attachment via `_send_calendar_email_for_crew(...,"invite")`. Email failures are caught and logged as `status="failed"` in the notification log — they don't 500 the request (unlike `respondToEventCrew`, which is a candidate for the same hardening). Auto-accepted self-invites are deliberately not notified.
- **Websocket**: emits `EVENT_CREW_UPDATED` once after the bulk commit (not per-row), so subscribers in other sessions refetch the roster wholesale.
- **Audit**: `invited_by_uuid` stamps every transitioned row; this is the field the Health page and roster diagnostics use to attribute invites.
- **Notification channels**: respects `person.preferences.notifications.channels` — SMS/WhatsApp goes through `notify_person`, email goes through the calendar-email path. The split is intentional; don't collapse them.
- **Auth**: `fetchApiAuthenticated` cookie session; `require_auth` + owner-relation guard on the handler.

## External consumers

- **Concorda iOS app** mirrors this endpoint for the owner's invite-pool screen. No scheduled jobs or webhooks call it directly.

## Open questions

- **Should the bulk path also pull declined rows forward?** Currently it's pool-only; an owner who wants to re-invite decliners has to enumerate uuids. UX hasn't been pushed on this.
- **Where should hard/soft cap warnings live** — client-side only, or should the server return a `warnings[]` array alongside the roster so all consumers (web, iOS) get consistent messaging without each reimplementing the slot-count math?
