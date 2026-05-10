---
node_id: concorda-web::src/lib/api.ts::adminOrgConfigApi.deleteLogo
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fc7ddd0026f58dec78aa53e8c976b25ae7e9ec2ec1745347e56e5ea93035853e
status: llm_drafted
---

# adminOrgConfigApi.deleteLogo

## Purpose

Removes the organization's logo from the server-side configuration. It is a specialized method of the `adminOrgConfigApi` object, used specifically to clear the existing logo asset. An agent should use this instead of `uploadLogo` when the intent is to revert to a default state or remove the branding entirely.

## Invariants

- **HTTP Method is `DELETE`** — The endpoint expects a standard DELETE request to `/api/admin/org-config/logo`.
- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the request includes a valid bearer token.
- **Returns `OrgConfigData`** — Upon success, the method returns the updated organization configuration object.

## Gotchas

- **Direct dependency on `AdminSystemPage`** — The `AdminSystemPage` (page.tsx:174) relies on this for administrative branding controls. If the return shape of the logo deletion changes, this page's state management may break.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires a valid session/token).
- **Audit**: N/A.
- **Side effects**: Deleting the logo affects the visual branding of the organization across the web app.

## External consumers

- `AdminSystemPage` in `concorda-web/src/app/members/admin/system/page.tsx`.
