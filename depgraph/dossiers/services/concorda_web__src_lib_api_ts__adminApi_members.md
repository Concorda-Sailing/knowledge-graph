---
node_id: concorda-web::src/lib/api.ts::adminApi.members
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e15fbae7aa790ee818d491471538d96e318277b6b204a1336e69a1fe99478ae4
status: current
---

# adminApi.members

## Purpose

Admin-only client-side mirror for the full member roster — returns paginated `Person` rows with PII (email, phone, mailing address, member category, shirt sizing) gated behind `org_admin` or `system_admin` via the router-level `_require_admin` dependency. Three components consume it: the user management grid (`AdminUsersPage`, with search/membership_type/year filters), the clubs admin page (`AdminClubsPage`, fetches `limit:100` to resolve delegate names by ID), and the club edit dialog (`ClubDialog`, fetches `limit:100` to populate the steward/delegate dropdown). Use this when an admin surface needs a list of people with contact info; do **not** reach for it from a member-facing view — directory/crewfinder go through privacy-respecting endpoints instead.

## Invariants

- Endpoint is mounted on a router with `Depends(_require_admin)` — every call is auth-checked for `org_admin` or `system_admin`. Do not relax this without revisiting all three callers and the privilege-escalation guard in `_require_can_modify_user`.
- Response shape is `{ total, skip, limit, members: Person[] }` — paginated. `total` is pre-pagination count; `members.length <= limit` (server caps `limit` at 100).
- `Person` returned here is the full PII shape (`email`, `phone_number`, `mailing_address`, `member_category`, sizes, `additional_email`/`additional_phone`). It is **not** the directory-safe shape — never feed this response into a non-admin-gated component.
- Server-side ordering is `last_name, first_name`. Callers that depend on stable ordering (e.g., the delegate dropdown alphabetization) get it for free; do not re-sort client-side without reason.
- `search` matches `first_name | last_name | email` (ILIKE). Phone, address, and member_category are **not** searched server-side.
- The two delegate-picker callers (`AdminClubsPage`, `ClubDialog`) hard-code `limit: 100`. If the org grows past 100 active people they will silently truncate — switch them to a typeahead or paginated picker before that happens.

## Gotchas

- The `year` filter joins on `Person.created`/`Person.leave_date` extracted years — it's an "active in year X" filter, not a "joined in year X" filter. Don't conflate them in UI copy.
- `membership_type` filter joins through `PersonProduct → TemporalProduct` on `slug`. If a slug is renamed, this filter silently returns zero rows; admin grid will look broken with no error.
- Recent commits in this file are unrelated (crew/schedule/coowner work) — no recent reverts on the members endpoint itself, but the file churns constantly so structural-hash drift is normal noise.
- `MembersResponse.members` is typed as `Person[]` in `api.ts`; the backend returns `PersonRead.model_dump()` which includes fields the frontend `Person` interface doesn't list (e.g., `additional_email`, `member_category`, `shirt_size`). They pass through silently — don't assume the TS type is exhaustive.

## Cross-cutting concerns

- **Auth**: Hard-gated by `_require_admin` (`org_admin` or `system_admin`). No org-scoping inside the query — a `system_admin` and an `org_admin` see the same global roster, which is the org_admin grandfather behavior tracked in `project_org_admin_grandfather.md`.
- **Audit**: No audit log on read. Reads of full PII are not currently tracked; if that becomes a requirement, this is the chokepoint.
- **Rate limits**: None specific. Lives behind the global rate limiter, which today requires single-uvicorn-worker (see `feedback_rate_limiter_single_worker.md`).
- **Side effects**: None — pure GET.

## External consumers

None known. No mobile app, no scheduled job, no webhook hits `/api/admin/members` — only the three web admin surfaces above.

## Open questions

- Should the `limit:100` callers (clubs page, club dialog) move to a dedicated lighter "people-for-picker" endpoint that returns only `{id, first_name, last_name}` and skips PII? The current pattern fetches full mailing addresses just to render a dropdown.
- Once Tier C scoping lands and `org_admin` is properly org-scoped, this endpoint needs an `organization_id` filter applied from `current_user` rather than returning the full global roster.
