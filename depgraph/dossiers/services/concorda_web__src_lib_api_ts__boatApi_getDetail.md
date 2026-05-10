---
node_id: concorda-web::src/lib/api.ts::boatApi.getDetail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f491b7c29db033f748a2db8e78200c937ead7720dceb7d56b9bec972245fe922
status: llm_drafted
---

# boatApi.getDetail

## Purpose
Authenticated client mirror for `GET /api/boats/{boat_id}/detail`. Returns a flat boat-row projection — `id`, `sail_number`, `name`, `manufacturer`, `boat_class`, `length`, `picture_url`, `banner_url` — gated to active crew and currently-invited crew. It is the "I'm on this boat, show me the boat" entry point. Distinct from `profileApi.getBoats` (caller's owned/crewed list, no per-boat fetch) and from the bare `boatsApi.lookup` row (sail_number+name probe with no auth gate). Despite framing as "full detail," the endpoint returns only boat fields — the three callers compose the full surface (`getDetail` + `getResume` + `getCrew`/`getPunchlist`) themselves via `Promise.allSettled`.

## Invariants
- Response shape is the flat 8-field projection above; if the backend grows a field the TS inline type at `api.ts:3146` must grow with it (no shared `BoatDetail` interface — each consumer redeclares it).
- 403 for membership status outside `{active, invited}` — declined, removed, prospective, and pool-only crew get rejected (see `boats.py:899`).
- Callers pair this with `getResume` and/or `getCrew` and tolerate partial failure via `allSettled`; `getDetail` failing is the hard fail (no boat to show), the others are soft.

## Gotchas
- The endpoint pre-dates the access-status tightening — earlier versions let any crew row read the boat regardless of status, which is why the comment at `boats.py:897` calls out blocking declined/removed/prospective explicitly. Don't loosen that guard without a logigraph rule.
- No `BoatDetail` is exported from `api.ts`; consumers each define their own `BoatDetail` interface and they have already drifted (e.g. `crew-boat-inline.tsx` doesn't track `banner_url`). Adding a field requires touching all three call sites or extracting a shared type.
- `getDetail` does NOT honor `rule::crew_visibility::peer_pii_resume_gated` — that rule applies to crew identities/resume, which live in `getCrew` / `getVisibleCrew` / `getResume`. The boat row itself has no peer PII. Don't conflate.
- Pending-invite consumers (`boat-invite-view.tsx`) rely on `invited` being readable; if you ever require `active` here, the invite-response screen goes blank.

## Cross-cutting concerns
- Auth: `require_auth` + crew-membership check. No org-admin override — even global admins without a crew row get 403.
- WebSocket: two of three callers refetch on `boat.updated` and `boat_crew.updated` via `useWsFreshness`. If you add a field whose source can change without firing those events (e.g. a punchlist-derived counter), it will go stale.
- No rate limiting beyond the global app limiter; no audit logging on read.
- No side effects.

## External consumers
None known. Web-only; the Expo app has its own boat-detail flow and does not call this endpoint as of 2026-05.

## Open questions
- Should this endpoint return `owner_person_uuids` / co-owner list? Today every consumer derives ownership by scanning `getCrew` for `role=owner`, which is a redundant round-trip.
- Worth introducing a shared `BoatDetail` TS type to stop the three-way drift, or is the looseness intentional?
