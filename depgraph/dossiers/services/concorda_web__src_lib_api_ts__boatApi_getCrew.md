---
node_id: concorda-web::src/lib/api.ts::boatApi.getCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a150b44c527da64728de6d605d8361598fd2a3963ddfce47acbe2e6f697602cb
status: current
---

# boatApi.getCrew

## Purpose

Client-side mirror for the boat-crew listing endpoint (`GET /api/boats/{id}/crew`). A thin `fetchApiAuthenticated` wrapper that returns every `BoatCrew` row for a boat — owners, active crew, prospective, invited, and declined — with a denormalized `person_*` block joined in. Used by 10+ React components/hooks across the boat page, dashboard cards, schedule detail, crewfinder drill-downs, and event-crew flows. Reach for this when a component needs the *full* roster (any status, any role) for a boat the viewer is already on; reach for `boatApi.getVisibleCrew` instead when you need the resume-gated peer view.

## Invariants

- Returns `BoatCrewMember[]` — never paginated, never wrapped in an envelope. Empty boat → `[]`.
- Every row carries `id`, `boat_uuid`, `person_uuid`, `role`, `status`, `priority`, plus `created`/`modified` ISO strings. Backend always populates these.
- `person_first_name`, `person_last_name`, `person_picture_url`, `person_email` are present **iff** the joined `Person` row exists. Treat them as optional in code paths that may run before a person is hydrated.
- `role` enum: `"owner" | "crew" | "prospective"`. `status` enum: `"active" | "prospective" | "invited" | "declined"`. New values must be added to the TS union in `BoatCrewMember` *and* checked at every consumer site — there is no exhaustiveness check.

## Gotchas

- **PII null-masking is server-side and contextual.** The `_crew_to_read` helper unconditionally attaches `person_email` when a Person row exists. There is no resume-gate on this endpoint — the gate lives on `/crew/visible`. Don't surface `person_email` in UI shown to non-owners without checking — the privacy contract is "you can see your crewmates because you're on the boat with them," which is weaker than the public crewfinder gate.
- **Auth: 403 for non-members.** Caller must be an `active` *or* `invited` BoatCrew member of this boat (`routers/boats.py:170`). Anonymous calls return 401 from `fetchApiAuthenticated`'s auth layer. `prospective` crew get 403 — surprising, since they show up in the response for others.
- **No backend `EventCrewMember` mixing.** Despite the name overlap, this returns `BoatCrew`, not `EventCrew`. Recent commits (`bf44b09`, `1b5d864`) tightened the per-event status type — don't reuse `EventCrewStatus` here.
- **`priority` is `getattr(crew, "priority", 0)`** server-side — older rows may default to 0; first-click ordering only applies to invites created after the priority system landed.
- **No cache invalidation hook.** Components that mutate via `addCrew`/`updateCrew`/`reorderCrew` must re-call `getCrew` themselves; there's no global store.

## Cross-cutting concerns

- **`rule::crew_visibility::peer_pii_resume_gated`** governs the *crewfinder* peer view (`/crew/visible`), **not** this endpoint. This endpoint is the in-the-tent view; the rule still matters because consumers like `crew-finder-panel.tsx` may render data from both shapes side-by-side and must not leak `person_email` from `BoatCrewMember` into a peer-only context.
- Frontend-side type to know about: `EventCrewMember` (api.ts:1695) is the schedule-side shape with `position_name`, `self_selected`, `resume_published`. Keep them disambiguated — same boat, different lifecycle.
- Auth layer adds the bearer token; rate limits hit the global per-user bucket, no endpoint-specific cap.

## External consumers

React components calling this directly (per depgraph):
- `src/app/members/crewfinder/crew/[id]/page.tsx::CrewDetailPage`
- `src/app/members/schedule/[id]/page.tsx::ScheduleEventDetail`
- `src/components/boat/boat-inline.tsx::BoatInline`
- `src/components/boat/boat-owner-view.tsx::BoatOwnerView`
- `src/components/boat/boat-page.tsx::BoatPage`
- `src/components/dashboard/boat-invite-view.tsx::BoatInviteView`
- `src/components/dashboard/crew-boat-inline.tsx::CrewBoatInline`
- `src/components/dashboard/event-crew-card.tsx::EventCrewCard`
- `src/components/dashboard/event-plan-panel.tsx::EventPlanPanel`
- `src/components/finder/crew-finder-panel.tsx::CrewFinderPanel`

Concorda iOS app does **not** consume this directly today — it uses higher-level event-crew endpoints.

## Open questions

- Should `person_email` be omitted from the response for non-owner viewers? The current contract leaks it to any active/invited crew member. No recent decision either way.
- Should `prospective` BoatCrew get read access? They currently 403, but show up in the list for others — asymmetric.
