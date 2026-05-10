---
node_id: concorda-web::src/lib/api.ts::profileApi.getBoatResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 30991e1575afaf2a3e22ec0e286c4bfbd382894d7e0ac789e9157742b46f4dff
status: current
---

# profileApi.getBoatResume

## Purpose

Client-side mirror for `GET /api/profile/boats/{id}/resume` — the boat's *competitive history and recruitment bio*, scoped to a single boat the caller owns. This is "boat-as-resume": the per-`Boat` recruitment profile (free-text `about`, ethos, positions wanted, race areas, `accepting_crew`, `published`) that drives the boat finder. It is NOT the person's sailing resume — for that, use `profileApi.getSailingResume()`. It is also NOT a per-race state — for the per-event "looking for crew" toggle, use `SailingEvent.accept_crew_requests`. Five web components consume it (dashboard, setup page, boat-inline, boat-owner-view, boat-setup-wizard), and the iOS app mirrors it. When asking "what does this captain want in crew, on this boat?" this is the right call.

## Invariants

- **Owner-only read.** The backend (`routers/profile.py:960-993`) requires the caller to have an `active`, `role=owner` row in `BoatCrew` for the requested `boat_id`; non-owners get 403. There is no peer-readable variant of this endpoint — peer reads of a boat's recruitment profile go through the public/authenticated boatfinder surface, which additionally requires `BoatResume.published == True`.
- **Path takes a boat id, not a resume id.** Resumes are looked up by `boat_id`; the `BoatResume` row's own PK is never exposed to the client.
- **404 on missing resume row OR missing boat.** The endpoint returns 404 for "boat not found" and 404 for "boat exists but no resume row yet" — the client cannot distinguish the two from the status code alone (the `detail` field differs).
- **Return shape matches `BoatResume` TS interface** (`api.ts`), which mirrors `BoatResumeRead`. Field renames require coordinated edits on web, API, and iOS.
- **Companion to the upsert at `PUT /api/profile/boats/{id}/resume`.** The PUT is upsert-style (creates on first save); the GET is not. Editor screens MUST treat 404 as "create new," not "error."

## Gotchas

- **404-on-missing-resume is the dominant footgun.** First-time owners have no row; a naive `await profileApi.getBoatResume(id)` throws. All 5 current consumers wrap in try/catch or `.catch(() => null)`. New consumers must follow suit.
- **Don't conflate `BoatResume.accepting_crew` with `SailingEvent.accept_crew_requests`.** Commit `b67d359` (and the underlying model fix `6c9b5f3`) split these — boat-level `accepting_crew` ("Yes"/"Occasionally"/"No") drives boat-finder display; per-race `accept_crew_requests` boolean drives the regatta-calendar Accepting-Crew badge. If a consumer of this endpoint surfaces a "looking for crew right now?" UI, it must compose both.
- **Distinct from `profileApi.getSailingResume()`.** Personal sailing resume lives on `Person`; boat resume lives on `Boat`. The two are not joined in the API response — a UI showing "this captain's preferences on this boat" needs both calls.
- **`published == True` is the boatfinder visibility gate, but this endpoint ignores it.** Owners always see their own draft resume here, even when unpublished. Code that surfaces this response to non-owners (don't — the endpoint is 403-gated, but copy-paste happens) must re-check `published`.
- **No client-side caching.** Each consumer fetches independently; setup wizard and boat-inline can issue concurrent identical fetches on a single page load.

## Cross-cutting concerns

- **Auth**: `require_auth` plus active-owner check via `_owner_query`. Co-owners with `status="pending"` are rejected — they cannot read the resume even though they are listed as owners.
- **WebSocket**: this `GET` does not broadcast. The paired `PUT`/`DELETE` (`updateBoatResume`, `deleteBoatResume`) broadcast `BOAT_RESUME_UPDATED` / `BOAT_RESUME_DELETED` from `routers/profile.py:1051,1090`. Consumers wanting live refresh subscribe to those events and re-call this `GET`.
- **Boatfinder coupling**: the response shape is the source of truth for what the boat finder will show once `published=True`. Edits in the boat-resume editor screens preview-render using this same shape.
- **Co-ownership coupling**: any co-owner with `status=active` can read AND edit the resume. There is no per-resume ACL; ownership of the boat is the sole gate.
- **No crew-visibility rule applies** here — this is the owner reading their own boat's data. Peer-facing reads happen on the boatfinder surface, which has its own rules.

## External consumers

- **Concorda iOS app** mirrors `GET /api/profile/boats/{id}/resume` in its boat-resume editor screen.
- 5 web call sites: `members/page.tsx` (dashboard), `members/setup/page.tsx`, `boat/boat-inline.tsx`, `boat/boat-owner-view.tsx`, `boat/boat-setup-wizard.tsx`.
- No scheduled jobs, no webhooks, no third-party integrations.

## Open questions

- **Should `GET` return `200 { resume: null }` instead of 404 for missing rows?** Same question as on `getSailingResume()`. All current consumers wrap in try/catch; a nullable return shape would simplify them and remove the boat-not-found vs resume-not-found ambiguity.
- **Should this endpoint also accept the boat's `slug` or only the UUID?** Boat-detail URLs in the web app use slugs in some places and ids in others; the editor screens currently resolve slug→id before calling this.
- **Should owner-side reads expose `published_at` (if it lands) so the editor can show "first published on…"?** Tracked on the `BoatResume` model open questions.
