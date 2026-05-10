---
node_id: concorda-test::lib/api-client.ts::ApiClient.getMyCrewData
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e92a6828dacb913172aaf2504e2a4123ce78bfbf0a76139e1de4c2529dc6294e
status: current
---

# ApiClient.getMyCrewData

## Purpose

Test-harness wrapper for `GET /api/profile/crew` — used by 3 Playwright specs (8 call sites across `dashboard/cross-context-crew`, `boats/coowner-shared-events`, `events/event-schedule`) to verify owner/crew/invitation state across boats. Mirrors the web client's `profileApi.getMyCrew` but exposes a deliberately narrower return type (only `owned_boats` and `crewed_boats`, each as `{ id, name?, sail_number }`) — the four-key richer shape the dashboard consumes (`invitations`, `event_invitations`) is dropped because no current spec asserts on those inboxes through this wrapper. Specs use it to look up a seeded user's boat UUID by `sail_number` mid-test (the sail number is the test-data identity; the UUID isn't known until after seeding) and to confirm a coowner accept/decline transitioned a boat from "neither side" into one of `owned_boats`/`crewed_boats`.

## Invariants

- Calls `GET /api/profile/crew`, authenticated via the bearer token previously set by `login()`. No query params; scope is always the current bearer's user.
- Returns a structural subset of the backend response — added/removed *backend* keys won't break this wrapper at runtime, only at type-assert sites in specs.
- `owned_boats[]` includes every boat the caller owns (sole or co-); `crewed_boats[]` only includes `role="crew"` + `status="active"` memberships. **Pending coowner-invite acceptance does not show up in either list until the invitation is responded to** — specs that need to observe the transition must call `respondToInvite` (or `respondToBoatCrewInvite`) and re-fetch.
- `sail_number` is always present and stable across the test run (it's the seed key); `name` is optional and may be absent for boats created via `lookupBoat` -> `requestCoowner` paths where the requester didn't set one.

## Gotchas

- The wrapper hides `invitations[]` and `event_invitations[]` from the response. If a future spec needs to assert "X has a pending crew invite for boat Y," **don't add the assertion via this wrapper** — either widen the return type here (and update all 8 call sites' inferred types) or reach for the dedicated invite-listing endpoints. The narrow shape was an intentional ergonomics choice for the existing specs, not a bug.
- `cross-context-crew.spec.ts` uses this wrapper across multiple personas in one test by calling `api.setToken()` between fetches. The wrapper carries no per-call auth; it relies on the caller to manage `this.token`. Tests that interleave personas without resetting the token will silently query the wrong user.
- Authoritative source for the response *shape* is the backend dict literal in `routers/profile.py:get_my_crew` — see the parent dossier (`profileApi.getMyCrew`). The wrapper's TS type can drift from reality; runtime won't catch it.
- Backend issues N+1 queries per call (documented in the parent dossier). Fine for E2E specs today, but a spec that loops `getMyCrewData()` per boat in a fixture will scale poorly — fetch once and cache.

## Cross-cutting concerns

- **Auth**: requires `setToken()` or a prior `login()` call; otherwise the underlying request returns 401 and `request<T>` throws.
- **TLS**: the module disables `NODE_TLS_REJECT_UNAUTHORIZED` process-wide on import — this wrapper inherits that and should never be imported by non-test code.
- **Side effects**: read-only. Safe to call repeatedly inside a single test without affecting state.
- **Datetime**: not exposed by the narrow return shape; the parent dossier's UTC-aware contract still applies if the type is widened.

## External consumers

None outside `concorda-test/`. Three spec files, all under `tests/`.

## Open questions

- Should the wrapper return the full four-key shape and let specs destructure what they need? Current narrowness saves a few type lines but blocks invitation-assertion specs from using it.
- `boats/coowner-shared-events.spec.ts` is the only spec calling it on a non-default `ApiClient` instance (`dan.getMyCrewData()`). Worth a brief comment in the wrapper that multi-persona tests are a supported pattern, so future Claudes don't "fix" it back to a singleton.
