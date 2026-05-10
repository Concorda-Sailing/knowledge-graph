---
node_id: concorda-api::models/role.py::UserRole
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b50eeeab1b8339ffd17cc74be1515f7607f9efedd44f41933c3dda2f88f7b6c4
status: current
---

# UserRole

## Purpose

`UserRole` is the join row between `Person` and `Role` that grants a person one of the seven seeded *system* roles, optionally scoped to a single `Organization`. The seven roles (defined in `scripts/seed_roles.py`) are `member` (level 10), `delegate` (20), `event_manager` (25), `treasurer` and `membership_admin` (both 30), `org_admin` (50), and `system_admin` (100). `Role.level` is a privilege ordinal used by the privilege-escalation guards in `routers/roles.py` (assign / revoke / edit-permissions) — a caller must hold a role at or above the target's level. Permissions are not stored on `UserRole`; they hang off `Role` via `role_permissions` (the 28-permission catalog in `seed_roles.py` covering events, directory, crewfinder, boatfinder, and admin.* categories). At request time `auth_middleware.AuthUser` loads every `UserRole` for the user, unions their permissions, subtracts `Person.disabled_permissions`, and exposes `has_role` / `has_permission` / `get_scoped_organizations` / `can_administer_orgs`. The optional `organization_id` is what makes a `delegate` "delegate of *this* club" or an `org_admin` "admin of *this* org"; a NULL value means global scope under the grandfather rule (see Gotchas).

## Invariants

- The seven role names in `seed_roles.py` (`member`, `delegate`, `treasurer`, `membership_admin`, `event_manager`, `org_admin`, `system_admin`) are referenced as string literals throughout the codebase. Renaming a seeded role is a multi-place change; deleting one is a breaking change.
- `Role.level` is the single source of truth for the privilege-escalation guards. `assign_role`, `revoke_role`, and `update_role_permissions` (`routers/roles.py:108,217,274`) all compute `actor_max = max(ur.role.level for ur in user_roles)` and reject `target.level > actor_max`. Adding a new role MUST set a level consistent with that ordering.
- `(person_id, role_id, organization_id)` is logically a uniqueness key — `assign_role` checks for an existing row before inserting (`routers/roles.py:227`). There is **no DB-level unique constraint** today; concurrent assigns can race-create duplicates. Code that iterates `user_roles` should tolerate duplicates.
- `organization_id` is nullable by design. `member`, `system_admin`, and `event_manager` are global roles (always NULL). `delegate` should always carry an org_id. `org_admin` *should* carry an org_id but historically does not — see grandfather gotcha.
- `assigned_by` is nullable so seed/migration code can create rows without a creator. Production assigns always populate it from `current_user.id`.
- Permission resolution always passes through `AuthUser.permissions`, which subtracts `Person.disabled_permissions`. Direct queries of `role.permissions` bypass that subtraction — don't reimplement permission checks against `UserRole.role.permissions` directly; use `AuthUser.has_permission`.

## Gotchas

- **Grandfather: NULL `organization_id` on an `org_admin` UserRole means global admin.** `auth_middleware.has_global_org_admin` and `can_administer_orgs` both treat a NULL-org `org_admin` row as a wildcard bypass for any `owning_org_ids` set. Per `project_org_admin_grandfather`, every existing `org_admin` row in production was created without an org_id; the bypass exists so they don't lose access. New `org_admin` UserRoles should be created *with* an `organization_id`, but the bypass remains until a backfill migration lands. Tightening the bypass without a backfill will lock real admins out.
- **Tier-C cross-org scope was a security finding (commit `058aa8c`, 2026-05-05).** Before that fix, having `org_admin` or `delegate` of *any* org let you mutate any *other* org's events, regattas, products, discounts, series, billing contacts, etc. — the routers checked role *type* but not `UserRole.organization_id`. The fix funnels every cross-org mutation through `AuthUser.can_administer_orgs(owning_org_ids)`. Any new mutating endpoint that touches an org-owned resource MUST resolve the resource's owning org set and pass it through that helper.
- **Privilege escalation through `update_role_permissions` (commit `33a37a3`).** `admin.roles.edit` permission was a foothold to grant arbitrary permissions to a higher-level role you could later be assigned to. The fix mirrors the level guard from `assign_role` onto the permission editor. Anyone adding a new "edit a role" surface needs the same guard.
- **Privilege escalation through admin user endpoints (commit `650233f`).** `org_admin` could take over a `system_admin` by resetting their password, deleting them, or rewriting them via CSV import. `_require_can_modify_user` is now the gate; new admin endpoints that mutate another user must call it.
- **`role.level` is *not* a strict total order.** `treasurer` and `membership_admin` are both level 30; `event_manager` (25) sits between `delegate` (20) and the 30s. Code that compares levels with `>` (strict) treats peers as non-grantable to each other. Code that uses `>=` does. The current guards are `>` (strict), intentional but easy to miss.
- **`require_role` checks role *name*, not *level*.** A level-100 custom role would not satisfy `require_role("system_admin")`. Most code prefers `require_any_role` or `require_permission`.
- **Permission deduplication is per-AuthUser-instance.** `AuthUser._permissions` is computed once per request from the eager-loaded `user_roles`. If you mutate `UserRole` rows mid-request (rare but happens in admin import paths), the cached set will be stale.

## Cross-cutting concerns

- **Auth middleware integration:** every authenticated request loads `UserRole` rows in `get_current_user` (`auth_middleware.py:145`) — one `SELECT * FROM user_roles WHERE person_id = ?` plus relationship lazy-loads of `role` and `role.permissions`. This is the hottest read on the model. Adding a column that triggers a join will hit every authenticated endpoint.
- **Permission system, not RBAC checks, is the public surface.** Routers should depend on `require_permission(...)` rather than `require_role(...)`. `require_role` still exists for the system_admin escape hatch and a few admin gates, but new code should hang authorization off `Permission.name` so that custom roles drop in cleanly.
- **`event_manager` is treated as equivalent to `system_admin` in admin gates** (`_require_manager` and `can_administer_orgs`'s first bypass). It is global-scope by design and bypasses org-scope checks. Adding a new role that should *also* bypass scope means editing those bypass lists.
- **System roles vs. relational roles — DO NOT confuse.** `UserRole` is for *system* roles (member, delegate, org_admin, etc.) and gates admin/UI surfaces. `BoatCrew.role` (`models/boat_crew.py`) is a *relational* role on a join table — values are `"owner"`, `"crew"`, `"prospective"`, scoped to a specific boat, and have nothing to do with `UserRole`. The co-owner rule (`rule::coowner::eligibility_at_accept`) gates promotion-to-owner on the **`boat_management` product grant** (a `TemporalProduct`), not on any `UserRole`. Same word, different model, different enforcement path.
- **Frontend mirrors `roles` and `permissions` from `/api/auth/me`.** UI gating reads the flat string sets, so role/permission *names* are part of the implicit API contract with `concorda-web` and the Expo iOS app.
- **No audit trail beyond `assigned_by` / `assigned_at`.** Revocations are hard deletes — there is no history of who-had-what-when. If audit becomes a requirement, this table needs soft-delete or a separate `user_role_audit`.

## External consumers

- **`concorda-web`** (`/api/auth/me`, `/api/roles/*` admin pages) reads role names and permission names verbatim — renames are app-breaking.
- **Concorda iOS Expo app** consumes the same `roles` / `permissions` arrays from `/api/auth/me`.
- **AI agent plugin / agent tokens** (`cga_*`): agent tokens authenticate as the issuing person and inherit that person's `UserRole` set. `require_session_auth` is the opt-out for endpoints that should never be reachable via agent token.
- **Seed scripts** (`scripts/seed_roles.py`) — fresh-install only per `feedback_deploy_no_data_mutation`. Re-deploys never re-seed roles.

## Open questions

- When does the `org_admin` NULL-org_id grandfather bypass get retired? It needs a backfill migration that assigns each existing `org_admin` row to the correct org and a follow-up that removes the NULL bypass from `can_administer_orgs`.
- Should `(person_id, role_id, organization_id)` get a real DB unique constraint? The application-level check is racy.
- Should role assignments be soft-deleted for audit? Today revoke is a hard `DELETE` and there is no history.
- Is the level ordinal granular enough? `treasurer` and `membership_admin` colliding at 30 is fine today but if a future role needs to slot between them the integer scale is awkward.
- Should `event_manager` *really* bypass org scope? For a federated multi-club deployment, an event manager probably wants org scope.
