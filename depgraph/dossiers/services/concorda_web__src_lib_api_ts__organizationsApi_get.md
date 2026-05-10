---
node_id: concorda-web::src/lib/api.ts::organizationsApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: de8540e49903c5dc93ff8fc043f8e051a04f78757c31ddfb36433a59aaae0d45
status: current
---

# organizationsApi.get

## Purpose
Client-side mirror for fetching a single Organization detail (yacht club / sailing org metadata — name, abbreviation, burgee URL, address, contact info, VHF channel, region, steward). Uses unauthenticated `fetchApi` since the backend `GET /api/organizations/{org_id}` has no auth guard — org metadata is treated as public-ish reference data inside the member portal. Used in three surfaces: the admin club editor page (`/members/admin/clubs/[id]`) to hydrate the edit form, the regatta detail panel to resolve `regatta.oa_uuid` into an organizer-name display, and the `ClubDialog` component for the edit-mode form. The thin pass-through shape (`(id) => fetchApi<Organization>(...)`) is deliberate — callers compose retry / cancellation / error handling at the use site.

## Invariants
- Returns the full `Organization` shape including nested `address` object, `burgee_url`, `vhf_channel` (number | null), `steward_id` — admin editor depends on every field being present to round-trip via `update`.
- Backend returns 404 when the org id is unknown; clients must handle that path (admin editor surfaces it as an error banner; regatta panel silently `.catch(() => {})` because a stale `oa_uuid` shouldn't break the page).
- No auth header is sent — must remain `fetchApi`, not `fetchApiAuthenticated`. Switching would break public-ish surfaces and introduce a token requirement the backend doesn't enforce.
- ID is treated as an opaque string (org UUID); do not URL-encode beyond template-literal interpolation — backend matches on `Organization.id` exact equality.

## Gotchas
- `regatta.oa_uuid` can be null/undefined — the regatta panel guards with `if (regatta.oa_uuid)`. New callers fetching org-by-foreign-key must do the same; passing `undefined` will hit `/api/organizations/undefined` and 404.
- `burgee_url` is whatever was stored (often a relative path or external URL). Don't assume an absolute URL when rendering — historical CSV imports populated mixed forms.
- Backend `GET` is unauthenticated but `PUT`/`DELETE` are gated by `_require_org_admin_scope`. A successful `get()` does not imply the caller can mutate — admin UI must independently check role before showing edit affordances.
- No caching layer — every consumer re-fetches on mount. Three calls on a page that shows multiple regattas from the same OA will stampede; if you add a cache, scope it carefully (org metadata changes when admins edit, no invalidation event exists today).

## Cross-cutting concerns
- No auth, no rate limit, no audit log on the GET path.
- No websocket invalidation; consumers re-fetch on their own lifecycle (mount, `clubId` change, `regatta.oa_uuid` change).
- Side effects: none — pure read. But callers often chain into `update()` (admin editor), which does require admin scope and emits no audit event of its own.

## External consumers
None known. Internal to `concorda-web`. The Expo iOS app does not currently call this endpoint directly.

## Open questions
- Should this endpoint require auth? Org metadata leaks burgee/contact-email/steward_id to anonymous callers who can guess UUIDs. Low risk (UUIDs aren't enumerable) but inconsistent with the rest of the org router.
- Worth a SWR/React-Query layer for org lookups by id? Three callers today, but the regatta list page could easily fan out to N orgs as regatta count grows.
