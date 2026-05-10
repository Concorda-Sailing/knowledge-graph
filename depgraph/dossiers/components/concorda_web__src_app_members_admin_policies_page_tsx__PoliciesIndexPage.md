---
node_id: concorda-web::src/app/members/admin/policies/page.tsx::PoliciesIndexPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 08f5cd929445286c9b8b3be5023ecf275a0d1af8d624c854425efeaa26cb2379
status: current
---

# PoliciesIndexPage

## Purpose

The central dashboard for managing organization-wide policies (Terms of Service, Code of Conduct, and Privacy Policy). It aggregates version history for all policy types via `adminPoliciesApi.listVersions` and displays the currently active version for each. This page serves as the entry point for administrators to review and publish new policy iterations.

## Invariants

- **Fetches all policy types in parallel** — Uses `Promise.all` to map over `POLICY_TYPES` and fetch version lists for each slug.
- **State is keyed by `PolicySlug`** — The `versionsBySlug` state must maintain a strict mapping of `[p.slug, rows]` to ensure the correct version history is displayed under the correct label.
- **Displays the active version** — The UI identifies the current version by finding the object in the array where `is_active` is true.
- **Error handling is top-level** — If the `adminPoliciesApi` call fails, the entire `error` state is populated with the error message, replacing the loading indicator.

## Gotchas

- **Material change side effects** — Per the UI text in line 69, publishing a new version with "material change" checked triggers a re-prompt for every member upon their next request. This is a high-impact action that affects the entire user base.
- **Loading state is mandatory** — The component returns a `Loader2` spinner while `loading` is true; failing to handle the loading state or the empty `versionsBySlug` state correctly will result in a flash of empty content or broken UI during the fetch.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges (implied by the `admin` path and `adminPoliciesApi` usage).
- **Side effects**: Publishing a "material change" triggers a global re-prompt for all members across the platform.

## External consumers

None known.
