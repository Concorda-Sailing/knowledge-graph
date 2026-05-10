---
node_id: concorda-web::src/lib/api.ts::adminTemporalProductsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a1d4cc7430fe50674216ae335933ff126f4d3a2989bd8d21b874dd3e937b787b
status: current
---

# adminTemporalProductsApi.list

## Purpose

Admin-only client-side mirror for the full temporal-products catalog — both `Membership` and `Event`-scoped products, across any year, including inactive rows. Wraps `GET /api/temporal-products` with the admin auth helper (`fetchApiAuthenticated`) and accepts `{year, category, include_inactive}` filters. This is the variant six admin surfaces consume (email compose, event detail, socials, per-category product page, users page, user dialog) when they need to render or pick from the *catalog* rather than what's currently buyable. Distinct from `temporalProductsApi.getAvailable`, which is the public/user-facing variant: that path filters to `is_active=true` and the current year and is read-only-public, while this admin path requires `admin.memberships.view` and is the **only** caller that can trigger the year-rollover lazy-copy.

## Invariants

- Hits `/api/temporal-products` (no `/available` suffix). The suffix split is the auth boundary — bare path = admin, `/available` = public. Don't merge them.
- Returns `TemporalProduct[]` (full admin schema with grants/event_id/dates/merchandise), not `TemporalProductPublic[]`. Consumers depend on the wider shape.
- Must use `fetchApiAuthenticated` — backend dependency is `require_permission("admin.memberships.view")`, an unauthenticated call 401s.
- Query construction uses `URLSearchParams` and only sets keys when truthy. `include_inactive=false` is sent by *omission*, not as `?include_inactive=false`. Backend treats absence as the default-false case; don't change to always-emit without checking the FastAPI `Query(False)` default.
- Backend ordering is `year DESC, sort_order ASC`. Consumers that render flat lists across years (e.g. `CategoryProductsPage`) rely on newest-first grouping.

## Gotchas

- **This call has a write side-effect.** When invoked with both `year` and `category` and the (year, category) bucket is empty, the backend runs `_copy_products_from_previous_year` and commits new rows before returning (`temporal_products.py:194-202`). A "list" call can mint a year's worth of catalog. The public `getAvailable` path used to do this too and was closed in commit `ec53704` (unauth DB write surface) — do not reintroduce lazy-copy on the public path, and don't assume this endpoint is idempotent.
- The lazy-copy only fires when **both** `year` and `category` are passed. Calling with `year` alone, or with neither, will return an empty list for a fresh year and silently do nothing — admins occasionally hit this and report "the new year is empty." The fix is to always pass `category` when the UI is category-scoped.
- `include_inactive` is the only way to see soft-deleted/disabled SKUs from the SPA. Forgetting it on an admin edit screen produces "the row vanished" reports when an admin toggles `is_active=false`.
- Returned `category` strings are capitalized (`"Membership"`, `"Event"`). Several callers compare to lowercase literals from URL slugs — normalize before comparing.
- Recent `feat(admin): add Health page surfacing pool stats and response times` (`37794d5`) and the drill-down drawer (`6fe57db`) didn't touch this function, but did add admin pages that call it; the admin surface area using this is still growing.

## Cross-cutting concerns

- **Auth**: `admin.memberships.view` permission gate. Org-admin grandfathering applies (NULL-org UserRole rows are global) — see `project_org_admin_grandfather.md`.
- **Year-rollover side effect**: described above. Triggers a `db.commit()` and refreshes; first admin to view a fresh (year, category) pair pays the latency. No event/websocket broadcast — other tabs won't know rows just appeared.
- **Entitlement contract surface**: each row carries the `grants_*` flags that downstream consumers (boat management gating, event discount eligibility) read. Admin UIs that toggle these flags effectively rewrite the entitlement contract — see TemporalProduct model dossier for the fan-out.
- **No rate limit, no audit log**. Mutations through sibling methods (`create`/`update`/`delete`/`reorder`) are unaudited; if audit lands, this read path is a natural place to attach view-tracking but currently is silent.
- **No websocket events**. Admin CRUD is silent broadcast-wise; the SPA refetches.

## External consumers

None directly — the iOS app and any third-party integration use `getAvailable` (public). This admin call is web-only.

## Open questions

- Should the lazy-copy be hoisted out of the GET handler into an explicit "Roll over year" admin action? A read with side effects is surprising and hard to reason about under concurrent admin loads.
- Should `include_inactive` default to `true` for admin surfaces? The current default mirrors public semantics, but admins almost always want the full catalog.
