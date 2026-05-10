---
node_id: GET::/api/admin/org-config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3d0fe0bbd3c0af1ad41ad3045bfdb5b6267a649a3f62930be8b55793ee1f4ca8
status: current
---

# GET /api/admin/org-config

## Purpose

Fetches the current organization-wide configuration settings. This is a read-only endpoint used to retrieve global metadata like the `app_title`, `error_notify_email`, and `logo_url`. Use this when a component needs to display branding or check the current state of organization-wide settings (e.g., the site title or the logo) without requiring write access.

## Invariants

- **Returns `OrgConfigResponse`** — the response shape is strictly defined by the `OrgConfigResponse` model.
- **Fallback behavior** — if no `OrgConfig` record exists in the database, the method returns a default object with `org_name="MBSA"` rather than a 404 or null.
- **Read-only** — this specific endpoint does not accept a body or change state; it is a pure `GET` request.

## Gotchas

- **Default value fallback** — per `73f8798 feat: configurable app title (default "MBSA Clubhouse")`, if the database record is missing, the system defaults to "MBSA".
- **Email configuration logic** — while this is a GET endpoint, the underlying schema (seen in `update_org_config`) treats an empty string as `None` to disable alerts. If you are building a UI to display these values, be aware that a "null" or "empty" email is a valid state for disabling notifications.

## Cross-cutting concerns

- **Auth**: None (publicly accessible to retrieve branding/config).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

- `concorda-web` (via `adminOrgConfigApi.get`)

## Open questions

- The `update_org_config` and `upload_org_logo` endpoints require `_require_system_admin`, but this GET endpoint is unauthenticated. Should the organization's internal configuration (like the error notification email) be visible to any authenticated user, or should it also be restricted to admins?
