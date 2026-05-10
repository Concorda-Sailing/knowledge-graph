---
node_id: concorda-web::src/lib/api.ts::profileApi.getSailingResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 01afd2a136f767c74f7323fd60f8b3756d29ea0bf7d180244c1473db2542beee
status: llm_drafted
---

# profileApi.getSailingResume

## Purpose

Client-side mirror for `GET /api/profile/sailing-resume` — the user's view of their *own* sailing resume. This is the editor entry point: every screen that reads, displays, or seeds the resume editor flows through here. It returns the full `SailingResume` shape (positions, race areas, certifications, availability, US/World Sailing IDs, the `*_ids` filter lists). When deciding "where do I get the current user's resume," this is the right call. For peer resumes (any other user's, on the crewfinder browse surface), use `crewfinderApi.detail(personId)` instead — different endpoint, different visibility rules, includes opt-in gating.

## Invariants

- **The endpoint 404s when no resume row exists** (`routers/profile.py:375-379`). It does not return `null` or an empty resume. Callers must either catch the rejection or accept that the promise rejects on first-time users.
- **Auth-required, scoped to `current_user.id`.** The backend filters by the authenticated user's id; there is no `personId` parameter and no way to fetch someone else's resume through this path.
- **No client-side caching layer.** Every call hits the network. The dashboard-badges hook, profile-inline, setup page, and regattas page all call independently — there can be 3-4 concurrent fetches of the same resume on a single page load.
- **Return shape matches `SailingResume` interface in `api.ts:2150`**, which mirrors `SailingResumeRead` on the backend. Field renames require a coordinated edit on both sides plus the iOS app.

## Gotchas

- **404-on-missing is the dominant gotcha.** 8 of 9 call sites either wrap in `.catch(() => null)` or live inside a try/catch. New consumers that naively `await profileApi.getSailingResume()` and use the result will throw on first-time users — always treat "no resume" as a normal state, not an error.
- **`null` from `.catch(() => null)` ≠ "user has no resume."** It also masks transient network errors and 401s. Callers conflate the two; if a logged-out user briefly hits these screens during auth state transitions, they read as "no resume" and may trigger setup flows.
- **Distinction from `crewfinderApi.detail(personId)`** (`api.ts:780`): that endpoint fetches *any* person's resume by id and is gated by the crewfinder opt-in (`Person.preferences.crewfinder.opt_in`) — it returns 403/404 if the target hasn't published. This endpoint has no such gate; you can always read your own resume row if it exists.
- **Distinction from `profileApi.getBoatResume(boatId)`** (`api.ts:1342`): boat resumes are a separate model (`BoatResume`) with their own endpoint — don't confuse "the boat's resume" with "the user's resume mentioning boats."
- **WebSocket `SAILING_RESUME_UPDATED` fires from `PUT` only**, not `GET`. Subscribers to the broadcast cannot rely on this fetch to re-emit; they must invalidate locally on the response.

## Cross-cutting concerns

- **Auth**: `require_auth` on the backend; no role/permission checks beyond login.
- **WebSocket**: paired write endpoint (`updateSailingResume`) broadcasts `SAILING_RESUME_UPDATED` keyed on `current_user.id`; the iOS app and dashboard badges subscribe to refresh after edits.
- **Profile completion / dashboard badges**: use the *presence* of availability days and `positions_preferred` to compute completion percentage and "needs setup" badges. Field renames on the resume can silently zero out completion scores.
- **Setup wizard** (`/members/setup`) calls this three times — once on load, twice after sub-step saves — to re-read the canonical state. Slow backends compound here.
- **Crew-visibility rule (`rule::crew_visibility::peer_pii_resume_gated`)** does not apply to this endpoint (own data), but consumers that pass the response into shared resume-rendering components should be aware that those components may also be used in peer-viewing contexts where the rule does apply.

## External consumers

- **Concorda iOS app** mirrors this endpoint via its own client; field-shape changes require app coordination.
- 9 web call sites (regattas page, setup page x3, profile-completion, profile-inline x3, use-dashboard-badges).
- No scheduled jobs, no webhooks, no third-party integrations.

## Open questions

- **Should `GET` return `null` instead of 404 for missing resumes?** The 404 pattern forces every caller to wrap in try/catch or `.catch(() => null)`, and the "no resume yet" state is a normal first-time-user condition, not an error. A `200 { resume: null }` shape would simplify all 9 consumers.
- **Should this be memoized at the `api.ts` layer or via a shared hook?** The dashboard currently issues 3-4 concurrent identical fetches. A `useSailingResume()` hook with SWR/React Query would dedupe, but the codebase doesn't lean on those libraries elsewhere.
