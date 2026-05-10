---
node_id: concorda-web::src/lib/api.ts::adminPoliciesApi.listVersions
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 97468321b960364cff683baf56d30de30dc2e140621dba2837e2a1da6acf4046
status: current
---

# adminPoliciesApi.listVersions

## Purpose
Admin-only client-side mirror for listing every persisted version of a policy (`tos`, `code_of_conduct`, `privacy_policy`) with acceptance counts attached. Backs the compliance/audit + version-management surface in `/members/admin/policies` — both the index card grid (one call per slug to compute "active version + N total") and the per-slug detail page (full history table + form pre-fill from the active row). It is the read-side counterpart to `publish` / `updateDraft`; UIs call it on mount and again immediately after publishing to refresh the table without a full page reload.

## Invariants
- Path stays `/api/policies/admin/{slug}/versions` (GET). Both the index page and the detail page hit it directly; there is no React Query layer caching the response.
- Slug is constrained to the `PolicySlug` union (`"tos" | "code_of_conduct" | "privacy_policy"`); backend `_validate_slug` rejects anything else with a 400.
- Returns `PolicyVersion[]` ordered newest-first (`Contract.created.desc()`). The index page picks the active row via `find(v => v.is_active)`, not via array position — do not change that to `[0]`.
- Each row carries `acceptance_count`, derived from `PersonContractAcceptance` joined on `contract_uuid`. Drafts (no acceptances) report `0`, never `null`.
- At most one row per slug has `is_active=true` — `publish_version` deactivates the prior active row in the same transaction. The detail page's version-suggestion logic and "Active" badge both assume this.

## Gotchas
- Permission split: this endpoint requires `admin.policies.view`, while `publish` and `updateDraft` require `admin.policies.manage`. A read-only admin can list versions but cannot publish — the UI doesn't currently disable the publish form for view-only callers, so it will surface a 403 from the manage call after a listVersions success. Don't conflate the two perms when adding gating.
- The detail page calls `listVersions` twice in a publish flow: once on mount (line 69) and again right after `publish` succeeds (line 110) to refresh the table. Any caching layer added here must invalidate on publish or that "just-published version appears" UX breaks.
- Empty list is a normal state (fresh slug with no draft yet) — both consumers handle `[]`. Don't 404 on no rows.
- The body field is returned in full on every list call (no pagination, no truncation). Three slugs × full ToS body per request is fine today but will get heavy if policies grow or list pagination is added — slim the response before that point.
- No recent commits touch this node directly; the surface has been stable since the policies admin shipped. Treat the lack of churn as "load-bearing for compliance," not "safe to refactor casually."

## Cross-cutting concerns
- Auth: `fetchApiAuthenticated` (cookie session). Anonymous callers get 401 from the wrapper before reaching the router.
- Audit: feeds the audit/compliance surface — `acceptance_count` is the legibility hook for "how many members accepted v1.2 before we superseded it." Don't drop that field.
- Side effects: pure read on the backend. No websocket events, no rate limiting beyond the global auth limiter.
- Data coupling: `Person.tos_accepted_at` is kept in sync by `accept_contracts` during the deprecation window; this endpoint reads `Contract` + `PersonContractAcceptance` only and is unaffected by that legacy mirror.

## External consumers
None known. Internal admin UI only — no mobile/Expo surface, no scheduled job, no webhook.

## Open questions
- Should `body` be omitted from the list response and fetched per-row on demand? Currently fine, but if policy bodies grow long the index page pays for three full bodies on every visit.
- Is there value in exposing this read to non-admin compliance roles (e.g., a future "auditor" perm) without granting `admin.policies.manage`? The split already exists at the perm layer; no UI uses it yet.
