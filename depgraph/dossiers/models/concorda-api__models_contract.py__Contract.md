---
node_id: concorda-api::models/contract.py::Contract
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: af2c3976fcbe404a306256337e2af3105a5cd8f58f8dd7d9ba4548dc9f58262b
status: llm_drafted
---

# Contract

## Purpose
Backend SQLAlchemy model for one version of a policy document — terms of service, code of conduct, or privacy policy. Each row is a self-contained version (`slug` + `version` + `body` + `effective_date`); the `is_active` flag selects the canonical row that the registration flow and acceptance-prompt logic will surface to members. Versioning is append-only — publishing a new version inserts a new `Contract` row and flips the prior row's `is_active` to false in the same transaction. Acceptances are recorded out-of-band on `PersonContractAcceptance` (one row per person per contract version), which is what powers the audit trail and the "needs to re-accept" prompt after a material change.

## Invariants
- At most one row per `slug` has `is_active=True`. `publish_version` enforces this by deactivating any prior active row in the same transaction before inserting the new one — do not bypass that path when seeding or migrating.
- `(slug, version)` is logically unique. The router rejects duplicates with 409 in both `publish_version` and `update_draft`; there is no DB-level UNIQUE constraint backing it, so application code is the only line of defense.
- Once *any* `PersonContractAcceptance` row references a `Contract.id`, that row is immutable. `update_draft` checks for acceptances and 409s — never edit `body`/`version`/`name` directly via a different path.
- `slug` is constrained at the router boundary to the `PolicySlug` union (`tos | code_of_conduct | privacy_policy`). The model column is a free `String(50)` — keep new slugs aligned with `_validate_slug` in `routers/policies.py` or callers will 400.
- `is_material_change=True` (default) means "re-prompt every member on next request"; setting it False intentionally suppresses that re-prompt. Default-true is the safe choice — flip it only for typo fixes.

## Gotchas
- `effective_date` is typed `Mapped[str]` but the column is `Date`; SQLAlchemy returns a `datetime.date` at runtime. The annotation lies — don't trust it for typing downstream code. Schemas in `schemas/policy.py` re-type it correctly.
- `Person.tos_accepted_at` is a legacy mirror still maintained by `accept_contracts` during a deprecation window. Two sources of truth coexist; the canonical one is `PersonContractAcceptance`. Don't add new readers of `tos_accepted_at`.
- Newest-first ordering for the admin versions list comes from `Contract.created.desc()`, not from `effective_date`. If you ever backfill historical rows with hand-set `created` timestamps, the admin UI's "active row" detection still works (it filters on `is_active`), but the table order will reflect insert time, not policy chronology.
- `__init__` hard-codes `type="Contract"` for the `BaseModel` polymorphic discriminator — don't pass `type=` from callers; it'll collide.
- Schema came from the `ee82e42` redesign; the versioned-policies feature landed in `da1589d`. Pre-redesign data living in `Person.tos_accepted_at` does *not* round-trip through this table.

## Cross-cutting concerns
- Auth: list/read of versions requires `admin.policies.view`; publish/update-draft require `admin.policies.manage` (split perm — see `adminPoliciesApi.listVersions` dossier). Member-facing reads (`GET /api/policies`, `POST /api/policies/me/accept`) require an authenticated session but no admin perm.
- Registration coupling: `POST /api/auth/register` reads every active `Contract` and inserts a `PersonContractAcceptance` per row at signup. Adding a new active slug therefore retroactively gates new registrations until they tick the box — coordinate the release.
- Audit: acceptance counts in the admin UI come from joining `PersonContractAcceptance` on `contract_uuid`. Don't soft-delete `Contract` rows; the audit surface assumes rows persist forever.
- No websocket events, no rate limiting beyond the global auth limiter, no scheduled jobs.

## External consumers
None known. Internal admin UI and registration/acceptance flow only — no Expo surface, no webhook, no scheduled job.

## Open questions
- Should `(slug, version)` get a real DB UNIQUE constraint? Application-level checks have held so far, but a race between two admins publishing simultaneously is theoretically possible.
- `is_material_change` currently has no consumer that branches on it beyond the re-prompt semantics — worth surfacing in the audit UI as "minor edit vs. material change" so compliance can tell them apart at a glance?
