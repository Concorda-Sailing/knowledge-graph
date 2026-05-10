---
node_id: concorda-web::src/lib/api.ts::organizationsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3df4c45f92eeec2fea1db2e07a5e7c9c2899f4128467dcd76206374f6c5d1005
status: current
---

# organizationsApi.list

## Purpose

Client-side mirror for `GET /api/organizations` — the unauthenticated organization list endpoint. It returns every `Organization` row in the federation as `Organization[]`, optionally filtered by a single `org_type` literal via querystring. Because it goes through `fetchApi` (not `fetchApiAuthenticated`), it works for logged-out visitors, which is why the public events page and the members-side directory both call it. It is the canonical "give me clubs" call: directory pages render it as the club list, OA pickers (regatta-OA cards, organizing-authorities-selector, preferred-organizations-selector, racing-preferences-section, club-affiliations) build their option sets from it, and the admin clubs page uses both the unfiltered list and the `org_type="Organizing Authority"` slice. New surfaces that need a club dropdown should reuse this rather than rolling a new endpoint.

## Invariants

- Response shape is `Organization[]` (`src/lib/api.ts:1788`) — full `OrganizationRead`, never a trimmed projection. Backend serializer is `schemas/organization.py::OrganizationRead`; any field add on the server must be reflected here or the TS type drifts silently.
- Endpoint is unauthenticated and unscoped. There is no `org_admin` filter, no membership filter, no soft-delete filter — it returns every row in the table, ordered by `name`.
- The `orgType` argument is passed through verbatim to `?org_type=` and the backend does an exact-match `==` filter (`routers/organizations.py:79–80`). It is **not** the directory triple — there is no built-in "member clubs only" mode here. Callers that want that filter client-side after the fetch (see `directory/page.tsx`).
- `org_type` values that callers actually pass: `"Organizing Authority"` (admin clubs page) and unfiltered. The directory triple (`"Yacht Club"`, `"Association"`, `"Sailing Center"`) is not a single querystring value — directory pages fetch unfiltered and then filter in JS.
- No pagination, no caching headers, no ETag. Every call is a full table scan. Acceptable today (~tens of clubs); becomes a problem if the federation grows past ~hundreds.

## Gotchas

- **Public-path leak surface.** Because the endpoint is unauthenticated, every field on `OrganizationRead` is world-readable. `contact_email`, `steward_id`, `billing_contact_id`, and `additional_data` ride along. If you add a sensitive column to `Organization`, exclude it from `OrganizationRead` or split a public schema — do not assume "members-only page" means "members-only data," because the same call serves the logged-out events page.
- **No retry / no error UI.** All five callers swallow errors with `.catch(() => {})` or land on a try/catch that sets empty state. A backend 500 silently produces an empty dropdown — users see "no clubs available" with no signal. Don't rely on this call to surface backend failures.
- **`org_type` is free-form.** The literal `"Organizing Authority"` in `admin/clubs/page.tsx:56` only matches rows whose `org_type` was spelled exactly that way at insert time. CSV import (`routers/organizations.py:143`) defaults missing types to `"Yacht Club"`, so OA-typed rows must be created deliberately. Misspellings produce empty result sets, not errors.
- **No `parent_org_id` traversal.** The list is flat. Callers wanting club hierarchy (parent/child relationships) must hit `organization_relationships` separately — this endpoint won't expand it.
- **Eight call sites, no shared cache.** Each consumer fires its own fetch on mount; navigating between directory → admin → regatta detail re-fetches the same data three times. There is no React-Query / SWR layer here.

## Cross-cutting concerns

- **Auth:** none required. Distinct from `organizationsApi.create/update/delete` which use `fetchApiAuthenticated` and are gated by `_require_admin` + `_require_org_admin_scope` on the backend (see `Organization` model dossier).
- **Tenant scoping:** none — returns all federation orgs regardless of viewer membership. The "Tier C cross-org scope" hardening (`058aa8c`) applies to mutating endpoints, not this read.
- **iOS app:** Concorda Expo app calls the same endpoint. Adding required fields to the TS `Organization` interface that the backend doesn't actually populate will break native rendering since both share `OrganizationRead` shape.
- **CSV / season-bundle:** indirectly — the orgs returned here are the same rows mutated by `importCsv` and the season-bundle pipeline. Slug stability (per Organization dossier) matters because external bundles round-trip via slug.
- **Datetime:** `created` / `modified` are UTC-aware (`UtcDateTime`) per `feedback_naive_datetime_convention`. Render via `formatInOrgTz`, not raw `Date` methods.

## External consumers

- **Concorda iOS app** (Expo) — same endpoint, same shape. Field renames are app-breaking.
- **Eight web call sites:** `app/events/page.tsx`, `app/members/events/page.tsx`, `app/members/directory/page.tsx`, `app/members/regattas/page.tsx`, `app/members/admin/clubs/page.tsx` (twice), `components/admin/organizing-authorities-selector.tsx`, `components/profile/preferred-organizations-selector.tsx`, `components/profile/sections/racing-preferences-section.tsx`, `components/profile/club-affiliations.tsx`.
- No known scheduled jobs, webhooks, or third-party integrations call `/api/organizations` directly.

## Open questions

- Should the endpoint require auth? Public exposure of `contact_email` and `steward_id` is a privacy posture choice that predates the multi-tenant hardening.
- Is a directory-filtered convenience param (`?member_clubs=true` collapsing the triple) worth adding, or do we keep the triple as a client-side concern? Today four call sites duplicate the filter logic.
- Pagination / shared-cache story is unspecified. If federation grows or a "show inactive clubs" toggle lands, this becomes the bottleneck.
