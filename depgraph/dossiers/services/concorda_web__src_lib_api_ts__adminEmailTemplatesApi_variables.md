---
node_id: concorda-web::src/lib/api.ts::adminEmailTemplatesApi.variables
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c5a291ec7fe37a1032a65777bbec9d95d7f926214c13b74e6e28b3d468fb4b21
status: llm_drafted
---

# adminEmailTemplatesApi.variables

## Purpose

Retrieves the list of available variables for the admin email template system. This is used to populate the UI for administrators to understand which dynamic placeholders (e.g., user names, event dates) can be injected into email templates. It is distinct from `preview`, which renders a specific template with actual data, whereas `variables` provides the schema of available keys.

## Invariants

- **Returns an array of `EmailTemplateVariable` objects.**
- **Requires authentication.** Uses `fetchApiAuthenticated` to ensure only authorized admins can access the template metadata.
- **GET request.** The underlying endpoint is a static GET call to `/api/admin/email-templates/variables`.

## Gotchas

- **UI Dependency.** The `EmailTemplatesPage` in `src/app/members/admin/email/templates/page.tsx` relies on this to show users what they can use in the template editor. Any change to the return shape will break the admin template builder UI.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: None.

## External consumers

None known.
