---
node_id: GET::/api/constants
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8178b13a1ad3e38dc8fbf82a87c2093543399a4822d5b7d271e06e9f8320da05
status: current
---

# GET /api/constants

## Purpose

Provides the foundational configuration and static metadata required to initialize the frontend. It returns organization-specific branding (name, logo, title, timezone) and static domain data (positions, experience levels, certifications, and boat templates). This is the primary endpoint used during the initial app load to ensure the UI matches the organization's specific identity and constraints.

## Invariants

- **Returns `ConstantsResponse`** — the schema includes `org_name`, `logo_url`, `timezone`, `default_membership_slug`, and `app_title`.
- **Fallback logic** — if no `OrgConfig` exists in the database, the endpoint falls back to environment variables (`ORG_NAME`, `ORG_LOGO_URL`) or hardcoded defaults (e.g., `"America/New_York"` for timezone).
- **`default_membership_slug` derivation** — if `org_config.default_membership_id` is present, it fetches the corresponding `TemporalProduct` to retrieve the slug; otherwise, it returns an empty string.
- **Data types are strictly typed** — `experience_levels` and `certifications` are instantiated from dictionary-based constants via the `ExperienceLevel` and `Certification` models.

## Gotchas

- **Hardcoded fallback values** — per commit `73f8798`, the `app_title` defaults to `"MBSA Clubhouse"` and the `timezone` defaults to `"America/New_York"` if the database record is missing.
- **Membership lookup dependency** — the `default_membership_slug` relies on a successful join with `TemporalProduct`. If the `default_membership_id` in `OrgConfig` points to a deleted or non-existent product, the slug returns empty.

## Cross-cutting concerns

- **Auth**: None (publicly accessible).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `concorda-web` to render branding and configuration-dependent UI elements like the `app_title` and organization-specific timezone-aware components.

## External consumers

- `concorda-web` (via `constantsApi.getAll`)
- `concorda-test` (via `ApiClient.healthCheck`)
