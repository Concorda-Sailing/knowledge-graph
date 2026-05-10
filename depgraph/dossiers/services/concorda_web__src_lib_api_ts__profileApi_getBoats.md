---
node_id: concorda-web::src/lib/api.ts::profileApi.getBoats
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 666f44d2335945e2ba8e02b7d9ab035adb4872dc18155110b439a50f0c52debf
status: current
---

# profileApi.getBoats

## Purpose

Client-side mirror for "what boats does this user own." Thin wrapper around `GET /api/profile/boats` that returns `Boat[]` for the authenticated caller — boats where the caller has a `BoatCrew` row with `role='owner'` and `status='active'`. This is the canonical fetch for "my boats" lists, ownership gates ("is this user a boat owner?"), default-boat selection in event/regatta flows, and exclusion filters in the boat/crew finders. Wrapped by the `useBoats` hook for component consumption; nine sites still call it directly (legacy or one-shot patterns). Prefer routing new consumers through `useBoats` so they pick up websocket-driven invalidation for free — direct callers fetch once and go stale until they refetch manually.

## Invariants

- Endpoint is `GET /api/profile/boats`, no params, response is `Boat[]`. The shape and URL are the contract — `useBoats`, twelve hook consumers, and nine direct consumers all assume this signature.
- "Owned" means `BoatCrew.role='owner' AND BoatCrew.status='active'` joined to `Boat`. Not the legacy `Boat.owner_ids` JSON column. Co-owners (also `role='owner'`) all see the same boat in their lists.
- Returns `Boat[]` (full model fields per `BoatRead`), never a paginated envelope. Adding pagination would silently truncate every consumer's "do I own a boat" check.
- `fetchApiAuthenticated` throws `Error("Not authenticated")` synchronously if no token is present — callers that swallow errors collapse "logged out" and "API down" into the same empty-array state.
- 401 from the backend bubbles as a thrown `Error` from `fetchApi`; consumers that don't `.catch` it will surface as unhandled promise rejections.

## Gotchas

- **Direct call vs `useBoats`**: calling `profileApi.getBoats()` directly gives you a one-shot fetch with no websocket invalidation. If a `BoatDialog` elsewhere edits a boat, your local state is stale until you refetch. The hook subscribes to `boat.updated` / `boat.deleted` and refreshes; raw API calls do not. Several of the nine direct consumers (`crewfinder-widget`, `regattas/page.tsx`, `events/new/page.tsx`) probably *should* be on the hook but predate it.
- **Returns owned-only, not crewed**: this endpoint is *not* "boats I'm associated with" — crew-only members get an empty list here. For that, use `/api/profile/crew` (which returns the richer `MyCrewData` with both `owned_boats` and `crewed_boats`). Confusing the two has bitten before.
- **No caching, no dedup**: each call hits the API fresh. A page that mounts three components calling this directly issues three round-trips. The hook doesn't help here either (no shared cache across hook instances).
- **`isBoatOwner` cascade**: many consumers compute `boats.length > 0` as the boat-owner gate (dashboard, profile-completion, setup wizard). A backend bug that drops the join condition silently flips every user to "not an owner" and hides the Boats tab — there is no error surface from this endpoint that consumers actually inspect.
- **Co-owner accept flow**: after accepting a co-owner invite, the new co-owner's `getBoats` should immediately include the shared boat. The `BoatCrew` row is inserted with `role='owner', status='active'` server-side; if a future change introduces `status='pending'` for co-owner accept, this endpoint must be updated or new co-owners will appear to "lose" their boat.

## Cross-cutting concerns

- **Auth**: requires Bearer token; `fetchApiAuthenticated` enforces token presence client-side, `require_auth` enforces session server-side. No org scoping — returns boats across all orgs the user owns in (rare but possible for multi-club members).
- **WebSocket**: this function itself emits nothing and listens for nothing. Invalidation lives in `useBoats` via `boat.updated` / `boat.deleted` event flags. Any backend mutation that doesn't publish one of those events will leave hook consumers stale; direct consumers are stale by default.
- **Audit / rate limits**: read-only GET, not rate-limited beyond global auth limits. No audit log entry.
- **Side effects on other features**: drives onboarding wizard step gating, dashboard tab visibility, boat finder self-exclusion, crew finder "my boats" filter, default-boat picker on new sailing events. A regression here cascades into onboarding, event creation, and finder UX simultaneously.

## External consumers

None known. Internal web app only. Native iOS app (Expo) hits the same endpoint via its own client; treat the URL and response shape as a public contract for that reason.

## Open questions

- Should the nine direct callers be migrated to `useBoats` for free websocket invalidation? `crewfinder-widget`, `regattas/page.tsx`, and `events/new/page.tsx` look like the strongest candidates.
- Should this endpoint return `crewed_boats` too, or stay strictly owned-only? Today the split between `/profile/boats` and `/profile/crew` forces consumers to know which question they're asking; a unified endpoint would simplify the finder and dashboard code.
- No org filter today — for users who own boats in multiple clubs, every boat comes back regardless of "current org" context. Unclear if that's intentional or just untested.
