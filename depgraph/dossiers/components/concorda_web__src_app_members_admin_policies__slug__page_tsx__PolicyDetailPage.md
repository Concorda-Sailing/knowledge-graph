---
node_id: concorda-web::src/app/members/admin/policies/[slug]/page.tsx::PolicyDetailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: abf8cb073094b4dd25da04ee5782db5aca6a78284379603258768d7259db6b62
status: llm_drafted
---

# PolicyDetailPage

## Purpose

The administrative interface for managing specific organizational policies (Terms of Service, Code of Conduct, or Privacy Policy). It allows admins to view version history, preview the current active version, and publish new versions. It is distinct from a read-only policy viewer by providing a form-based workflow to update the `name`, `version`, `body`, and `effective_date` of a specific policy slug.

## Invariants

- **Slug validation is strict.** The `slug` must be one of `tos`, `code_of_conduct`, or `privacy_policy` via `isValidSlug`.
- **`effectiveDate` uses organization timezone.** It is initialized using `utcIsoToOrgDateInput` to ensure the date input matches the org's local context rather than the browser's.
- **`suggestedVersion` is auto-calculated.** It finds the highest existing numeric version and increments it by 1.0 to prevent manual versioning errors.
- **Form pre-fills on mount.** The `name` and `body` are automatically populated from the current active version to support "minor edit" workflows.

## Gotchas

- **Timezone-aware date input.** Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone. The `effectiveDate` state must be handled via `utcIsoToOrgDateInput` to avoid the "browser-local" drift fixed in that commit.
- **Version incrementing logic.** The `suggestedVersion` logic relies on `parseFloat` and `Math.max`. If a version string cannot be parsed as a finite number, it defaults to `"1.0"`.

## Cross-cutting concerns

- **Auth**: Requires admin-level permissions (implicitly handled by `adminPoliciesApi`).
- **Audit**: Updates to policies via `adminPoliciesApi.publish` trigger an error log entry (per commit `86ff361`).
- **Side effects**: Updating a policy affects the public-facing rendering of that policy across the web app.

## External consumers

None known.
