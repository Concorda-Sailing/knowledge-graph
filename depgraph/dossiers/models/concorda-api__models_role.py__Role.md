---
node_id: concorda-api::models/role.py::Role
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8537a3a62a2bfa535b615983d9dad4d594a8223de2c64db828ec9e873cd63930
status: current
---

# Role

## Purpose
Backend SQLAlchemy model for the permission-role layer of Concorda's authz system. A `Role` is a named bundle (e.g. `system_admin`, `org_admin`, `delegate`, `member`) with a `level` integer (higher = more privileged) and a many-to-many set of `Permission` rows attached via the `role_permissions` junction table. Roles are not assigned to people directly — the `UserRole` join row (person, role, optional organization, assigner, assigned_at) is what grants a role to a person, optionally scoped to one org. Future Claudes editing here are touching the spine of every `require_*` dependency in the API: a wrong invariant here silently widens or narrows access across all routers.

## Invariants
- `Role.name` is unique and is the stable string key consumed by code (`user.has_role("system_admin")`, seed scripts, role lookups in `routers/roles.py` and `routers/admin.py`). Renaming a role is a data migration, not a code change.
- `Role.level` orders privilege monotonically — `system_admin > org_admin (50) > delegate (20) > member`. Level is what `assign_role` and demotion/promotion guards compare; flipping the ordering breaks the privilege ladder silently.
- `Permission` is a first-class row joined via `role_permissions` (many-to-many). It is **not** a JSON list on `Role` — any code or migration that assumes JSON-on-role is wrong. `PUT /api/roles/{id}/permissions` rewrites the junction.
- `UserRole.organization_id` is **nullable on purpose**: a NULL means "global / unscoped." Tier C scoping treats NULL as a grandfather bypass for `org_admin` (see `project_org_admin_grandfather`); changing the column to NOT NULL would lock out every existing org_admin, all of whom were created via `routers/admin.py` paths that don't set org_id.
- `(person_id, role_id, organization_id)` should be effectively unique — there's no DB constraint enforcing it, but `assign_role` and the admin user-create/update paths assume one row per (person, role, org). Duplicate rows will multiply privilege checks and break revocation.
- `Role` rows are seeded, not user-created at runtime. There is no `POST /api/roles` to mint new roles; the catalog is fixed by seed + migration.

## Gotchas
- The git log on this file is shallow (two commits, both bulk additions) — most of the hard-learned behavior lives in the routers that consume it (`routers/roles.py`, `routers/admin.py`, `routers/auth.py`) and in the IDOR audit trail. Read the dossiers there before reshaping this model.
- `level` is an `Integer` with `default=0`, so a misseeded role silently lands below `member`. New roles must specify `level` explicitly in the seed.
- `UserRole.assigned_by` is nullable and FKs `persons.id` — system-seeded roles (registration, import) leave it NULL. Don't add a NOT NULL constraint without backfilling.
- The relationship `permissions` is loaded lazily; iterating `role.permissions` inside a request that's about to commit can trigger an N+1. Hot paths (`get_current_user`, role-check dependencies) should eager-load.
- `Permission` lives in this same file despite the filename — don't split it without updating every `from models.role import Permission` import.

## Cross-cutting concerns
- **Authorization spine.** Every `require_role`, `require_permission`, and `require_org_scope`-style dependency reads through `Role` + `UserRole`. A migration that drops/renames a column here is a global outage.
- **Tier C org scoping (in flight).** Cross-org enforcement keys off `UserRole.organization_id IS NULL` as the global-bypass signal for `org_admin`. Removing that nullability or its semantics needs the grandfather-migration project to land first.
- **Registration / admin user create / import.** `POST /api/auth/register`, `POST /api/admin/users`, and `POST /api/admin/users/import` all create `UserRole` rows; they currently do **not** populate `organization_id` for `org_admin`, which is the source of the grandfather problem.
- **Audit.** `assigned_by` + `assigned_at` are the only audit trail for role grants — there's no separate audit log table for role changes. Don't drop these columns.
- **Seeding.** Roles + permissions are populated by the seed step; on a fresh install they must exist before the first user is created or `has_role` checks blow up.

## External consumers
None known directly. The Expo iOS app and any external integrations consume role state only through the API endpoints listed in the dependents section — they do not touch this model. The seed scripts and migration system are the only non-router consumers.

## Open questions
- Should `(person_id, role_id, organization_id)` get a real unique constraint? Today it's enforced only by router code.
- After Tier C ships and the grandfather migration runs, can `UserRole.organization_id` become NOT NULL with a `system_admin` role carrying global scope instead? See `project_org_admin_grandfather`.
- `Role.level` is unbounded; do we want named tiers (enum-like) to keep the ladder legible, or is the integer good enough?
