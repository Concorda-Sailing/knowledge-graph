---
node_id: concorda-api::models/person_contract_acceptance.py::PersonContractAcceptance
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: de0cc2e26bd4cb71aeefeeceb4a906803430aa2c259170d9bba3ac6a6f3fc18f
status: current
---

# PersonContractAcceptance

## Purpose
Backend SQLAlchemy model recording one (person, contract version) acceptance — written when a member tics the TOS / code-of-conduct / privacy checkbox at registration, or re-accepts after `is_material_change` flips on a new `Contract` row. Append-only audit row: `person_uuid` + `contract_uuid` + `accepted_at` (UTC) + optional `ip_address`. It is the canonical source of truth for "has this member accepted policy X version Y" and the join target that produces `acceptance_count` on the admin versions list. The legacy `Person.tos_accepted_at` is a denormalized mirror still maintained during the deprecation window — every new reader should consult this table, not the Person column.

## Invariants
- Append-only. Never UPDATE or DELETE an existing row — the audit/compliance surface assumes rows persist forever and `update_draft` (PATCH `/api/policies/admin/versions/{id}`) treats *any* row referencing a contract as an immutability seal on that contract.
- Logically unique on `(person_uuid, contract_uuid)`. `accept_policies` enforces idempotency by pre-querying existing rows and skipping inserts; `auth/register` only inserts for active contracts at signup time. No DB-level UNIQUE backs this — application code is the only line of defense.
- `accepted_at` is a UTC-naive `datetime.utcnow()` at write time (both call sites). Treat it as UTC despite the lack of timezone-aware storage — consistent with the codebase-wide UtcDateTime convention.
- `ip_address` is `String(45)` to fit IPv6; nullable because background/internal flows (none today, but reserved) may write without a request context.
- `contract_uuid` references a `Contract.id` that must exist. `accept_policies` 404s if any submitted id is missing; there is no FK constraint, so orphaning is a real risk if a `Contract` row is ever hard-deleted (which it should never be — see Contract dossier).

## Gotchas
- Two write paths, slightly different semantics: `auth/register` writes one row per *currently active* contract at signup; `policies/me/accept` writes one row per *explicitly submitted* `contract_uuid`, which is how the re-accept-after-material-change flow works. Don't unify them without preserving both behaviors.
- `accept_policies` also reaches across and mutates `Person.tos_accepted_at` when a ToS slug is among the accepted contracts — the legacy mirror is kept in sync here, not via a trigger. If you stop calling this path you'll desync the deprecated column.
- `__init__` hard-codes `type="PersonContractAcceptance"` for the `BaseModel` polymorphic discriminator — never pass `type=` from callers; it'll collide.
- Schema came from the `ee82e42` redesign; pre-redesign acceptances live only in `Person.tos_accepted_at` and were not backfilled into this table. Don't write code that assumes a row exists for every pre-2026 ToS-accepting member.
- `accepted_at` is typed `Mapped[str]` but the column is `DateTime` — the annotation lies, SQLAlchemy hands back `datetime`. Mirrors the same annotation drift on `Contract.effective_date`.

## Cross-cutting concerns
- Auth: writes require an authenticated session (`require_auth` on `/me/accept`) or the registration flow's own gating. Reads happen only inside admin endpoints gated by `admin.policies.view` (see `adminPoliciesApi.listVersions` dossier) — there is no member-facing read of this table.
- Audit: the entire compliance surface (admin versions list, "N members accepted v1.2") joins on `contract_uuid` and counts rows here. Soft-deleting or pruning would silently corrupt those counts.
- Registration coupling: adding a new active `Contract` slug retroactively gates new registrations — `auth/register` inserts a row per active contract and the form must collect a checkbox for each. Coordinate Contract publication with the registration UI.
- No websocket events, no rate limiting beyond the global auth limiter, no scheduled jobs, no Expo surface.

## External consumers
None known. Internal admin compliance UI, registration flow, and `/policies/me/accept` only — no webhook, no scheduled job, no mobile client.

## Open questions
- Should `(person_uuid, contract_uuid)` get a real DB UNIQUE constraint? Current idempotency relies on the pre-query in `accept_policies`; a double-submit race could theoretically insert duplicates.
- Should `contract_uuid` get a real FK to `contracts.id`? Today nothing prevents orphan rows if a `Contract` is hard-deleted, which is exactly the kind of footgun a future refactor might step on.
- Once the `Person.tos_accepted_at` deprecation completes, the sync block in `accept_policies` can go — no ticket tracks that cleanup yet.
