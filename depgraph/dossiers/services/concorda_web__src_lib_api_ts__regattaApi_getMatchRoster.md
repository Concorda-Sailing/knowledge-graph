---
node_id: concorda-web::src/lib/api.ts::regattaApi.getMatchRoster
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6e5018deff30dfcdf534dbe9b9de36474a98e932dcdff9f2741456f83a824b6c
status: current
---

# regattaApi.getMatchRoster

## Purpose

Client-side mirror of `GET /api/regattas/{id}/match-roster` — returns the two-list `MatchRoster` of (a) registered boats with their crew status and (b) crew prospects who have the regatta on their schedule but aren't matched to a boat. Despite the "roster" name, the three consumers don't use it to print a printable race-officer roster; they use it as a live finder feed: the regatta detail panel renders both lists for browsing, the looking-for-crew sailor sees boats accepting requests, and the captain's "find crew" sheet pulls the crew list to invite from. Each section is independently permission-gated server-side, so callers must handle either list being empty by policy, not just by data.

## Invariants

- Response shape is always `{ boats: RosterBoat[], crew: RosterCrew[] }` — both keys present, either may be `[]`.
- `boats` is empty unless the caller has `boatfinder.view`; `crew` is empty unless they have `crewfinder.view`. Caller with neither permission gets HTTP 403, not an empty object.
- `accept_crew_requests` on each `RosterBoat` is the per-`SailingEvent` toggle, not a regatta-wide flag — drives the "Accepting crew" badge in consumers.
- `slots` is the live `BoatConfig` slot count (denominator); `accepted_count` is accepted `EventCrew` rows. Consumers compute "X of Y" badges from these — don't substitute `positions_open.length`.
- Crew list excludes anyone who is (a) marked captain on this regatta (explicit `PersonEvent.role='captain'` or legacy NULL-role bookmarker who owns one of the regatta's boats) or (b) already accepted on any sailing event for the regatta.

## Gotchas

- Multi-day regattas: `_build_boat_roster` keeps the *first* `SailingEvent` per boat for `positions_open` — a known v1 limitation. If multi-day regattas appear, this under-reports openings vs. the `boats_looking` count from `compute_match_counts`. The two endpoints can diverge.
- Captain exclusion was the subject of `4f90038 fix(match-counts): exclude bookmarkers who own a boat from crew prospects` — the legacy-NULL-role inference exists only because old bookmarks predate role tagging. New code paths should write explicit roles (`7e6ed14`).
- `b67d359 fix(regattas): drive Accepting-Crew badge from per-race toggle` and `6c9b5f3` both moved away from regatta-wide accept flags. Don't reintroduce a regatta-level accepting-crew field — the badge is per-`SailingEvent` and the roster reflects that.
- Owner display is `"First L."` via `_format_owner_name`, with graceful degradation when parts are missing — don't assume a full name.

## Cross-cutting concerns

- Auth: `require_auth` plus permission check; cross-org Tier C scoping (`058aa8c`) gates regatta visibility upstream.
- No rate limit, no audit, no websocket emission — pure read.
- Tightly coupled to `compute_match_counts` (same module): the two must stay in sync on what counts as "looking" / "available" or the regatta detail panel and list-card badges disagree.
- PII: returns `picture_url`, partial names, experience level, years sailing for crew. Callers without `crewfinder.view` never see these — gate is server-side, but client UIs should still avoid logging the response.

## External consumers

None known. No mobile/Expo callers, no scheduled jobs, no webhooks. Three internal web consumers only (regatta detail panel, crew-schedule "boats looking" card, captain's find-crew sheet).

## Open questions

- Should multi-day regattas aggregate `positions_open` across days, matching `boats_looking` semantics? Deferred until real multi-day data exists.
- The "race officer printable roster" use case implied by the endpoint name doesn't have a consumer yet — is that planned, or should the endpoint be renamed to reflect its actual finder role?
