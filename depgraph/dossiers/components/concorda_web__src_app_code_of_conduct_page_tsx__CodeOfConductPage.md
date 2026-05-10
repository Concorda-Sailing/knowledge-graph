---
node_id: concorda-web::src/app/code-of-conduct/page.tsx::CodeOfConductPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 90b1d7839d61794ad7897fee587ebdbee97a4cb43885ce94d9f325c53c3255c1
status: current
---

# CodeOfConductPage

## Purpose

A thin routing wrapper that renders the `PolicyPageView` component with the `code_of_conduct` slug. It serves as the entry point for the public-facing Code of Conduct page, ensuring the correct policy content is fetched and displayed via the centralized policy engine.

## Invariants

- **Hardcoded slug**: The `slug` prop is fixed to `"code_of_conduct"`. Changing this value without a corresponding entry in the CMS/API will result in a 404 or empty policy view.
- **Component dependency**: Relies entirely on `PolicyPageView` for layout, data fetching, and error handling.

## Gotchas

- **Versioned UI requirement**: Per commit `86ff361`, this page is part of the "versioned policy UI" rollout. Any changes to the layout must be made within `PolicyPageView` to ensure consistency with other versioned policies (e.g., Privacy Policy or Terms of Service).

## Cross-cutting concerns

- **Auth**: None. This is a public-facing route.
- **Side effects**: None.

## External consumers

None known.
