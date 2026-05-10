---
node_id: concorda-web::src/app/members/admin/email/templates/page.tsx::EmailTemplatesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f7e53a1425fdb9f2905347556e7341b70451877b8ec060621f48f6086befa55d
status: llm_drafted
---

# EmailTemplatesPage

## Purpose

The administrative interface for managing system-wide email templates and their associated variables. It provides a CRUD interface for editing the name, subject, body, and description of templates, as well as managing the list of available template variables. This is the central control point for any automated email content sent by the system.

## Invariants

- **Requires `adminEmailTemplatesApi`** — all data fetching and mutations rely on this specific API client.
- **Mandatory fields** — `name`, `subject`, and `body` must be non-empty strings to pass the client-side validation in `handleSave`.
- **State reset** — `openCreate` must explicitly reset the `form` to `EMPTY_FORM` and clear `editingId` to prevent data leakage from a previous edit session.
- **Variable handling** — `variables` is expected to be an array of strings; the component handles the mapping from the API response to the local state.

## Gotchas

- **Mobile layout constraints** — per commit `0564f06`, admin dialogs must cap width and stack the footer on `<md` breakpoints to prevent UI breakage on mobile devices.
- **Silent refresh failure** — the `refresh` function in `useEffect` catches errors silently; if the API is down or the user lacks permissions, the loading state will resolve, but the template list will simply be empty without user feedback.

## Cross-cutting concerns

- **Auth**: Requires administrative-level permissions (implied by the `adminEmailTemplatesApi` dependency).
- **Side effects**: Changes to these templates directly impact the content of all system-generated emails (e.g., crew invites, registration confirmations).

## External consumers

None known.
