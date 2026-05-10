---
node_id: concorda-web::src/hooks/use-boats.ts::useBoats
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dc2a96a6de06801d08ac56c43ed12e0ef790c9cc97345a2c1efc99fa41f9f69d
status: current
---

# useBoats

## Purpose

Canonical hook for fetching the current authenticated user's owned boats. It wraps `profileApi.getBoats()` with React state, exposes `{ boats, isLoading, refresh }`, and self-invalidates on `boat.updated` / `boat.deleted` websocket signals so any tab that mounts it stays in sync after edits made elsewhere (another browser, another component, the boat dialog, etc.). Use this hook anywhere a component needs "what boats does *this* user own" — boat finder, crew finder, schedule planning, dashboard, setup wizard, and the inline boat editor all rely on it as the single source of truth, so prefer it over ad-hoc `profileApi.getBoats()` calls.

## Invariants

- Return shape is stable: `{ boats: Boat[], isLoading: boolean, refresh: () => Promise<void> }`. Twelve+ consumers destructure these names; renaming requires a sweep.
- `boats` is never `null`/`undefined` — it starts as `[]` and resets to `[]` on fetch error. Consumers can call `.map`, `.length`, `.find` without null-guards (and many do).
- `isLoading` starts `true` and flips `false` exactly once after the first fetch settles (success *or* failure). It does not flip back to `true` on websocket-triggered refetches — UIs that render skeletons only see them on first mount.
- A failed fetch is silently swallowed (the comment is "User may not be authenticated yet"). The hook never throws and never surfaces an error string.
- `refresh` is stable across renders (`useCallback` with `[]` deps), so passing it to effects' deps lists is safe.

## Gotchas

- The websocket-refetch `useEffect` has **no dependency array** — it runs on every render. It's a deliberate poll-the-context pattern (`isDirty` reads a shared flag, `clearDirty` resets it so only one consumer triggers the refetch), but it means: (a) every render does an `isDirty` check, and (b) if you ever wrap this in `React.memo` or move the dirty check, the refresh will silently stop firing.
- Errors are swallowed. If the API starts returning 500s, `boats` will appear empty and downstream UI will render "you have no boats" states (e.g. setup wizard steps, "isBoatOwner = boats.length > 0" gates). There is no error channel to surface this.
- Each component that calls `useBoats()` owns its *own* fetch — there is no shared cache. A page that mounts `BoatInline`, `EventPlanPanel`, and the dashboard `boats` tab simultaneously will issue three `GET /profile/boats` calls on mount. SWR/React-Query is *not* in play here.
- The hook returns *owned* boats only (whatever `profileApi.getBoats()` returns for the logged-in user). It is not a generic boat lookup — `BoatDetailPage` uses it to know "is this *my* boat" by ID intersection, not to fetch the boat being viewed.
- `crew-finder-panel` builds `myBoatIds` from this hook on every render without memoization; cheap today but a footgun if `boats` ever grows large.

## Cross-cutting concerns

- **Auth**: depends on `profileApi.getBoats()`, which requires a session cookie. Pre-auth renders silently return `[]` rather than waiting — fine for public pages that happen to mount it, dangerous if a consumer assumes "empty list" means "no boats owned" rather than "not logged in yet".
- **WebSocket**: subscribes to `boat.updated` and `boat.deleted` event flags via `useWebSocket().isDirty`. The backend emits these on boat CRUD; any new boat-mutating endpoint must publish one of those event types or this hook will go stale. Does *not* listen for boat creation events directly — relies on the caller (e.g. `BoatDialog`) to call `refresh` after create.
- **Boat model coupling**: returns `Boat[]` from `@/lib/api`. Any field added to `Boat` flows through here automatically; any field removed will break consumers that destructure it from `boats[i]`.
- **Side effects on other features**: `boats.length > 0` is the canonical "is this user a boat owner" check on the dashboard and setup wizard, gating tab visibility and wizard steps. A regression here cascades into onboarding flow.

## External consumers

Internal-only (no external apps consume the hook itself — they hit the API directly). Twelve in-repo callers as of the last commit, representative slice:

- `src/app/members/page.tsx::DashboardPage` — gates `isBoatOwner` and the Boats tab.
- `src/app/members/setup/page.tsx::SetupPage` — drives the onboarding wizard's boat steps.
- `src/components/boat/boat-inline.tsx::BoatInline` — uses `refresh` (aliased `refreshSidebar`) after edits/deletes to keep the boat list sidebar fresh.
- `src/components/dashboard/event-plan-panel.tsx::EventPlanPanel` — picks a default boat for new sailing events (`boats.length === 1` shortcut).
- `src/components/finder/crew-finder-panel.tsx::CrewFinderPanel` and `boat-finder-panel.tsx::BoatFinderPanel` — exclude the viewer's own boats/crew from search results.
- Plus boat/crew detail pages, schedule detail, schedule tab, and `boat-owner-view`.

## Open questions

- Should this migrate to SWR/React-Query to deduplicate the N concurrent fetches per page mount? The websocket-dirty pattern would need to translate into cache invalidation.
- Should `isLoading` re-assert on websocket-driven refetches, or is "stale data while refreshing" the intended UX? Today it's the latter by accident, not design.
- The swallowed-error branch makes "logged out" and "API down" indistinguishable. Worth surfacing an `error` field for the dashboard gate at least.
- No commits beyond the initial dashboard-overhaul touch this file — the websocket-dirty integration has not yet been stress-tested against rapid edits or multi-tab scenarios.
