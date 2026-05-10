---
node_id: concorda-api::models/organization.py::Organization
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ccd783b83da7a5b24ed0e0f7de32aa3aa91ec8c062e67eecab0eb6337e030df6
status: llm_drafted
---

# Organization

## Purpose

An `Organization` is a club, association, or sailing center in the Concorda federation — the multi-tenant unit that owns events, regattas, series, products, member directories, and crew finders. Concorda is built around an MBSA-like federation: one central org plus many member yacht clubs. `Organization` is the row those clubs live in. It is the *external* tenant boundary; `OrgConfig` is the singleton for the *hosting* deployment's branding and runtime knobs (timezone, app title, rate limits) and is unrelated to per-club tenancy. People affiliate with orgs via the `person_organizations` M2M (`models/junction_tables.py`); orgs own/co-own events via `OrganizationEvent` (the multi-OA join, see `services.organizing_authorities.get_owning_org_ids_for_event`); admin scope is keyed on `UserRole.organization_id` (see `auth_middleware.AuthUser.can_administer_orgs`). When deciding where club-scoped data lives, default to `Organization.id` as the foreign key and a join table for many-to-many; do not add another implicit "owning club" column to a domain model.

## Invariants

- `name` and `org_type` are the only non-null business columns. `org_type` is a free-form string today, but `routers/organizations.py:50` and `routers/admin.py` filter on the literals `"Yacht Club"`, `"Association"`, `"Sailing Center"` to identify directory-eligible clubs. Treat that triple as the canonical "member club" set.
- `slug` is globally unique when non-null. Used by `season-bundle` upsert (`08e2d33`) as the natural key — do not change a slug once any external import or AOL bundle references it.
- `region` is one of three buckets — North / Central / South — per migration 058 (`88820d7`). The earlier 4-bucket scheme (incl. "Boston") was rebucketed; the canonical list is exposed via `routers/constants.py`. Adding a fourth region is a multi-place change.
- `abbreviation` is nullable but indexed; it is the human handle used in regatta OA cards and event filters (`bbe1627`). Keep it short (≤20 chars) and stable.
- The "legacy columns" comment block (`billing_contact_id`, `steward_id`, `fleet_captain_id`, `burgee_url`, `reciprocity_with`, `parent_org_id`) is **misleading**. The schema doc commit `cf7f495` declared these migrated to `organization_contacts` / `organization_relationships` / `additional_data`, but `steward_id` is still actively read by `routers/organizations.py:58` and `routers/admin.py:184,782` to resolve the club delegate, and all six are still in `schemas/organization.py` and accepted on create/update. They are dual-write zombies; treat them as live until a real removal commit lands.
- Members M2M uses `person_organizations` with `lazy="selectin"` on both sides — symmetric load mode is required to avoid N+1 on directory pages.

## Gotchas

- **Cross-org IDOR is a recurring footgun.** Commit `058aa8c` (security: tier-C cross-org scope enforcement) closed an audit finding that any `org_admin` of any club could rename/delete another club's organization row or swap its billing contact. The current `routers/organizations.py` PUT/DELETE/contacts endpoints rely on `_require_org_admin_scope(org_id, user)` → `AuthUser.can_administer_orgs({org_id})`. Any new mutating endpoint on this model MUST go through that helper. The base `_require_admin` only checks role *type*, not scope.
- **Grandfather: NULL-org_id `org_admin` UserRole = global admin.** Per `project_org_admin_grandfather` and `auth_middleware.py:79–100`, existing `org_admin` rows historically had no `organization_id`, so `can_administer_orgs` treats NULL-scope as a wildcard bypass. New `org_admin` UserRoles should always carry an `organization_id` — but do not assume existing ones do, and do not "tighten" the bypass without coordinating a backfill.
- **`Organization` rows seed at deploy time on fresh installs only.** Commit `9d46445` ("seed delegate organizations on fresh install") is fresh-install seeding; per `feedback_deploy_no_data_mutation`, re-deploys must not mutate org data. If you add a new mandatory column, write a migration — do not lean on seeders to fill it.
- **Two separate "is this org admin" checks exist.** `_require_admin = require_any_role("org_admin", "system_admin")` (role-type only) and `_require_org_admin_scope` (org-scoped). Many endpoints use BOTH as a dependency + manual call combination. Mixing them up has historically been the bug.
- **`address` is a free-form JSON dict** (`{street, city, state, zip}`), not a structured column. CSV import/export at `routers/organizations.py:91–113,143–151` hard-codes those four keys. Adding new address fields means updating both directions.
- **`additional_data` is the dumping ground for displaced columns** (`burgee_url` etc. per `cf7f495`). It is read by client code in unpredictable ways. Treat reads as best-effort and writes as scoped to the surface that owns the key.
- **No cascade on delete.** Deleting an `Organization` does not cascade to `OrganizationEvent`, `UserRole`, `person_organizations`, or `organization_contacts`. The DELETE endpoint at `routers/organizations.py:213` relies on the DB and SQLAlchemy defaults; orphaned rows are real. Future "My Crew delete guard" pattern (warn-and-cascade per `project_my_crew_delete_guard`) likely applies here too.

## Cross-cutting concerns

- **Auth / scoping:** `AuthUser.can_administer_orgs(set)` is the single chokepoint for cross-org mutation. `services.organizing_authorities.get_owning_org_ids_for_event/_regatta/_series/_product` is how downstream resources resolve "which orgs own this." Combine OA join *and* the legacy `Event.organizing_club_id` so events predating multi-OA still resolve.
- **Directory scoping:** `org_type in ("Yacht Club", "Association", "Sailing Center")` is the public-directory filter (`/api/organizations/delegates`, `routers/admin.py`). Clubs of other types are invisible to members. `feat(directory): include sailing centers and racing associations` (`45f2bec`) widened this set; widen carefully.
- **Calendar / timezone:** Per `feedback_naive_datetime_convention`, all datetimes are UTC-aware via `UtcDateTime`. Org-scoped UI rendering uses the *deployment's* `OrgConfig.timezone` (commit `6c314f5` — render .ics + email body in the org timezone). `Organization` itself currently has no timezone column; if a federated club needs a non-MBSA TZ, that's a new feature, not a bugfix.
- **Email / notifications:** `Organization.contact_email` is read by `routers/admin.py` bulk-email send (`POST /api/admin/email/send`). Bulk-email rate limit was hardened in `5f9a046`; new mass-send paths must respect it.
- **CSV import/export:** `routers/organizations.py:84–167` implements both directions. Import dedupes on `name` (not `slug`), and silently skips rows whose name already exists. Adding a new column means updating header rows, writers, and reader.

## External consumers

- **Concorda iOS app** (Expo) consumes `/api/organizations`, `/api/organizations/delegates`, and embeds `OrganizationRead` inside event/regatta payloads via `OrganizingAuthoritySummary`. Field renames or removals are app-breaking — coordinate.
- **Calendar feeds** include the org name + abbreviation as the event organizer label.
- **`season-bundle` upsert pipeline** (`08e2d33`) uses `slug` as the upsert key for organizations and series — external bundle authors are coupled to slug stability.
- **Admin CSV import/export** is consumed by club admins via the web UI; column order is part of the contract.

## Open questions

- When does the "legacy columns" block actually get dropped? `steward_id` is still the source of truth for the delegate lookup despite the schema doc claiming migration to `organization_contacts`. A real cutover plan is missing.
- Should `Organization` carry its own `timezone` (and locale) for federated multi-club hosting, or remain implicitly tied to `OrgConfig.timezone`? Today the deployment is single-tenant MBSA so the question is academic, but multi-tenant hosting would force it.
- The `org_admin` NULL-org_id grandfather bypass needs a follow-up backfill (per `project_org_admin_grandfather`). No ticket cuts off when that's safe to remove.
- `parent_org_id` is still on the model but no router queries it; the canonical "parent" relationship moved to `organization_relationships`. Safe to drop, but no migration drafted.
- Delete cascade story is unspecified — should deleting an `Organization` block on existing `OrganizationEvent` / `UserRole` rows, or cascade-clean them? Today it does neither cleanly.
