---
node_id: concorda-web::src/components/policy-page-view.tsx::PolicyPageView
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b0855f48e4272dd50bcd5e48f03c9327b5dd6e204e36327d9098bc53d46460ad
status: current
---

# PolicyPageView

## Purpose

Renders a single, versioned legal policy page (e.g., Terms of Service, Privacy Policy) by fetching data from the `policiesApi`. It handles three distinct states: a loading state, a successful render of the Markdown body, and a "not yet published" state. This component is the primary view for users to read organizational legal documents.

## Invariants

- **Fetches via `policiesApi.get(slug)`** — The component relies on this specific API method to retrieve the `PolicyDetail`.
- **Renders Markdown content** — The `policy.body` is passed directly into the `<Markdown />` component for rendering.
- **Displays version metadata** — The header must always show both the `version` and the `effective_date` to ensure legal clarity.
- **Requires a valid `PolicySlug`** — The `slug` prop determines which specific document is fetched and displayed.

## Gotchas

- **"No active version" is a soft error** — Per the logic in the `catch` block, if the error message contains `"no active version"`, the UI displays the `NOT_YET_PUBLISHED_TITLES` placeholder rather than a hard error. This prevents a 404 from looking like a system failure to the user.
- **Hardcoded titles** — The `NOT_YET_PUBLISHED_TITLES` record maps specific slugs (e.g., `tos`, `code_of_conduct`) to human-readable strings; if a new policy type is added to the API, it must be added here to avoid an empty title during the "not published" state.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: Y (Per commit `86ff361`, this component is part of the "error log admin" feature, implying policy fetch failures or access issues are tracked via the admin error log).
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
