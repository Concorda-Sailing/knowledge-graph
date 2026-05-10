---
node_id: concorda-web::src/components/regatta/regatta-detail-sections.tsx::LinkSlot
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 55c889798702eb8d85dfa3138ec6dbcce88e460d20a2c227e901cfbd26898c77
status: current
---

# LinkSlot

## Purpose

A helper component used to render external links (like NOR, SI, or Registration URLs) within the regatta detail view. It handles the logic for transforming raw strings into valid URLs and manages the visual state of the link. It is distinct from a standard `<a>` tag because it provides a fallback "disabled" button state when no URL is present and can optionally wrap URLs in an authentication-aware resolver.

## Invariants

- **`href` is the source of truth.** If `href` is null or undefined, the component renders a disabled, opaque button with a trailing em-dash (`—`).
- **`authed` flag controls URL resolution.** When `authed` is true, the `href` is passed through `authedUrl(href)` to ensure the link is compatible with the authenticated session.
- **Protocol fallback.** If `authed` is false and the string does not start with `http`, the component prepends `https://` to ensure the link is absolute.
- **Target behavior.** All active links are forced to `target="_blank"` with `rel="noopener noreferrer"` for security and to prevent navigation away from the app.

## Gotchas

- **Layout shift on empty links.** Because the component renders a `Button` with a specific size (`sm`) and a hardcoded em-dash when `href` is missing, the width of the "LinkSlot" can change significantly between a populated and empty state.
- **Promotion to top of panel.** Per commit `3aada74`, this component (and the row it lives in) was promoted to the top of the detail panel to ensure critical documents like NOR and SI are immediately visible to users.

## Cross-cutting concerns

- **Auth**: Uses `authedUrl` when the `authed` prop is true to resolve authenticated routes.
- **Side effects**: The visibility and state of these links directly impact the "Documents & Links" row in the regatta detail panel.

## External consumers

None known.
