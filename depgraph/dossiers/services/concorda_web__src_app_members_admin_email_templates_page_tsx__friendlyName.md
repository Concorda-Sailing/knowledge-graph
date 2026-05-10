---
node_id: concorda-web::src/app/members/admin/email/templates/page.tsx::friendlyName
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b1b8dc908779c1f2c975eb871a2b4601519512be7850de3c55e90864be4228b1
status: current
---

# friendlyName

## Purpose

The `friendlyName` utility converts snake_case or kebab-case strings into Title Case for UI display. It is used to transform raw API identifiers (like `invite_link_template`) into human-readable labels (like `Invite Link Template`) within the Admin Email Templates management page.

## Invariants

- **Input is a string.** It expects a raw string identifier.
- **Output is Title Case.** It replaces underscores with spaces and capitalizes the first letter of every word.
- **Pure function.** It does not rely on external state or the `Intl` object; it is a deterministic string transformation.

## Gotchas

- **Mobile layout constraints.** Per commit `0564f06`, admin dialogs (which use this name for headers/labels) must cap width and stack footers on `<md` screens to prevent UI breakage.

## Cross-cutting concerns

- **Auth**: Requires admin-level permissions via `adminEmailTemplatesApi`.
- **Side effects**: Changes to template names or subjects via this page's forms will affect the visual output of any automated emails sent to users.

## External consumers

None known.
