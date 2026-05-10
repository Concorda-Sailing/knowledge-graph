---
node_id: POST::/api/events/slug/{0}/register
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a986f9affd8a633625a1f500a615ac970cbde5773ce8bfc92625caa677948689
status: current
---

# POST /api/events/slug/{slug}/register

## Purpose

Endpoint handler for public event registration via slug — the form-submit target on the public events landing page (`/events/[slug]`). Looks up the `Event` by slug, validates the chosen `Product` (ticket type), enforces members-only / deadline / capacity / payment gates, and writes one `EventRegistration` row tying the registrant (authenticated `person_id` or anonymous email) to a `Transaction` if the ticket is paid. Auth is optional: anonymous users can register for free or anonymously-paid tickets, but `members_only` events 401 without a session. This is the public counterpart to the admin `/api/events/{id}/registrations` GET — the only write path a non-admin uses to land a row in `EventRegistration`.

## Invariants

- Event lookup is by **slug**, not id — slugs are non-unique across personal events (commit `4fd165d` dropped slug on personal events to avoid a global UNIQUE collision), so a slug query may match an Event the caller didn't intend if a future change reintroduces collisions.
- `members_only` events require an authenticated `current_user`; anonymous callers must be rejected with 401 *before* any payment lookup.
- `registration_deadline` comparison uses tz-aware UTC (`datetime.now(timezone.utc)`); `Event.registration_deadline` must remain tz-aware (UtcDateTime) for the comparison to be meaningful — naive datetime would raise.
- Capacity check counts only `status == "Confirmed"` registrations against `product.quantity`; pending/cancelled rows must not occupy a seat.
- For paid tickets (`product.price > 0`): the `Transaction` must be `Completed` AND `transaction.person_id == current_user.id` (or both NULL for anon). This binding is load-bearing security — without it any caller could replay another user's completed txn id. Do not relax.
- A single `Transaction` may back up to `transaction.expected_quantity` Confirmed registrations; further reuse must 400.
- Duplicate guard is `(event_id, product_id, email, status=Confirmed)` — same email cannot double-register for the same ticket type, but *can* register for different tickets on the same event.
- The created row carries `person_id` only if the caller is authenticated; anon registrations are identified by email only.

## Gotchas

- **Stripe lazy-confirmation fallback** (lines 1710–1724): if the txn isn't yet `Completed` but has an `external_reference`, the handler calls `retrieve_payment_intent` and promotes `pending_txn.status = "Completed"` inline, committing mid-handler before the registration insert. This means a successful register call has the side effect of finalizing a Transaction row — surprising for callers expecting a pure read+insert. The `except Exception: pass` swallows Stripe errors silently; debugging a "Payment not completed" 400 may require looking at Stripe logs, not the API.
- The identity-binding logic uses `expected_person_id = current_user.id if current_user else None` for *both* the strict and the fallback query. An anonymous caller cannot use a logged-in user's pending txn even if they know the id — good — but it also means a user who paid while logged-out and then logged in *cannot* complete registration with the same txn. No recent fix for this; flag if a user reports it.
- Slug, not id, in the URL — but `Product.event_id` filter uses the resolved `event.id`, so a slug pointing to the wrong event still can't accidentally consume another event's tickets.
- No git log noise specific to this handler in the recent 15 commits; the surrounding churn is all schedule/crew. Treat the handler as quiescent — but the Transaction binding logic is recent enough (the security comment at line 1698–1701 reads as post-incident) that it deserves caution on edits.

## Cross-cutting concerns

- **Auth:** optional via `get_current_user`; `members_only` flips it to required. No permission check beyond that — this is the deliberately-public surface.
- **Rate limits:** none on this route. Anonymous registration is a plausible spam vector (free tickets, bogus emails); the `(event_id, product_id, email)` dedupe is the only throttle. See the "Rate limiter requires single uvicorn worker" memory if adding one.
- **Side effects:** writes `EventRegistration`; may mutate `Transaction.status` and `Transaction.payment_method` via the Stripe fallback path; may emit a Stripe API call (`retrieve_payment_intent`). No email/webhook fires from this handler — confirmation email, if any, is downstream of `EventRegistration` creation elsewhere (verify before assuming).
- **Audit:** none beyond the row itself; no audit log table is written.
- **Schedule visibility:** new `EventRegistration` rows surface in `my-schedule` via `registered_events` query (events.py:228). A registration is immediately visible to the registrant on next schedule fetch.

## External consumers

None known. The four direct dependents are all in concorda-web (`page.tsx` calls × 2, `eventsApi.register`, `eventsApi.registerAuthenticated`). The Expo iOS app does not currently surface a public-event registration flow. No webhooks or scheduled jobs.

## Open questions

- Should the silent `except Exception: pass` around `retrieve_payment_intent` log to the audit/error stream? Currently a Stripe outage looks identical to "user never paid" from the 400 response.
- Should anonymous → authenticated txn handoff be supported (user pays anon, then logs in to register)? Current binding rejects it; product intent unclear.
- No capacity reservation between the sold-out check (line 1683) and the insert (line 1756); two concurrent registrations could both pass the count check and oversell by one. Not observed in production but theoretically possible under load — depends on whether the DB/transaction isolation we're running closes the gap.
