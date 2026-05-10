---
node_id: concorda-web::src/lib/api.ts::temporalProductsApi.getAvailable
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 594006a91d53ed4006eb652243ce6d4c02c579c6f546b4fc3e469464917963cf
status: llm_drafted
---

# temporalProductsApi.getAvailable

## Purpose

Public, unauthenticated client-side mirror for what's currently buyable — wraps `GET /api/temporal-products/available` via `fetchApi` (no auth helper) and returns `TemporalProductPublic[]`. Backend filters to `is_active=true` and the requested year (defaulting to `datetime.now().year` server-side if the caller omits it). This is the variant four user-facing surfaces consume to render purchase options: `JoinPage` (membership tier picker), `RegisterPageContent` (post-invite signup), the profile `MembershipUpgrade` tab, and — somewhat unexpectedly — `AdminSystemPage` for a public-facing sanity check. Distinct from `adminTemporalProductsApi.list`: that path requires `admin.memberships.view`, returns the wider `TemporalProduct` shape (grants flags, dates, merchandise), and is the *only* path that may trigger the year-rollover lazy-copy.

## Invariants

- Hits `/api/temporal-products/available` (with `/available` suffix). The suffix split is the **auth boundary** — bare `/api/temporal-products` is admin, `/available` is public. Don't merge them.
- Returns `TemporalProductPublic[]` — narrower shape than admin (no `grants_*` flags, no `event_id`, no merchandise associations). Consumers that need entitlements must not rely on this endpoint.
- Uses `fetchApi`, **not** `fetchApiAuthenticated`. This call must work for logged-out visitors hitting the join page; switching to the auth helper breaks anonymous signup.
- Backend filter is hard-coded to `is_active=true`. There is no `include_inactive` escape hatch on this path and there shouldn't be — the endpoint exists to advertise *currently buyable* SKUs.
- Backend ordering is `sort_order ASC` only (no `year DESC` — the year is already filtered to one value).
- Year defaults to current year *server-side*; the client's `?year=` is optional. Don't push the default into the client — keeping it server-side means the rollover happens automatically at midnight Jan 1 without an SPA rebuild.

## Gotchas

- **Lazy-copy was deliberately removed from this path** in commit `ec53704` (security fix — unauthenticated DB write surface). The handler docstring at `temporal_products.py:165-167` calls this out. If a fresh year has no active products, this endpoint returns `[]`, and the join page will look broken until an admin lands on a category-scoped admin list (the only remaining lazy-copy trigger) or runs duplicate-year. **Do not reintroduce auto-copy here.**
- Symptom of the above: on Jan 1 of a new year, the join/register pages may show an empty product list before any admin has logged in. Fix is admin-side, not by relaxing this endpoint.
- `category` is supported by the backend as a query param but **not** plumbed through this client wrapper — only `year` is. If a consumer needs category filtering, either add the param here or filter client-side; don't half-add it.
- `AdminSystemPage` (a dependent) calls this *public* variant rather than the admin list. That's intentional — it surfaces the public catalog as a smoke test — but means changes to the public shape ripple into an admin diagnostics page.

## Cross-cutting concerns

- **Auth**: none. Anonymous-callable. This is the only way an unauthenticated visitor sees pricing.
- **Side effects**: none. Pure read. (Contrast with admin list, which can mint a year of rows.)
- **Rate limiting**: not currently rate-limited. Public endpoint with DB query — a natural target if abuse appears. Note rate-limiter is single-worker today (`feedback_rate_limiter_single_worker.md`).
- **Caching**: no HTTP cache headers set. Each pageview is a DB hit; small table, fine for now.
- **No websocket events, no audit log.** Admins toggling `is_active` won't notify open join-page tabs; users see stale lists until refresh.

## External consumers

None known directly. The iOS Expo app does its own membership flow against the same endpoint family but — as of this writing — call patterns haven't been audited to confirm whether it hits `/available` or the admin list with a token. Worth verifying before changing the public response shape.

## Open questions

- Should the empty-on-rollover failure mode be fixed by an admin-triggered "publish next year" action that copies+activates, rather than relying on someone happening to load the admin catalog?
- Should `category` be added to the client wrapper now that join and upgrade flows are diverging (membership vs event purchases)?
