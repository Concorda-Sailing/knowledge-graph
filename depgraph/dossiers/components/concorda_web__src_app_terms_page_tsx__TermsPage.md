---
node_id: concorda-web::src/app/terms/page.tsx::TermsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0aad4133c81e077529fbc8cb3bb2dfb4f91cef67b414717f03a33c0484a29314
status: llm_drafted
---

# TermsPage

## Purpose

A thin wrapper around `PolicyPageView` that serves the Terms of Service (ToS) page. It exists to provide a dedicated route for legal documentation, specifically passing the `"tos"` slug to the underlying view component.

## Invariants

- **Uses `PolicyPageView` as the base component.** This page does not contain its own layout logic; it relies entirely on the slug-based rendering of the parent view.
- **Hardcoded slug.** The `slug` prop is fixed to `"tos"`.

## Gotchas

- **Versioned UI dependency.** Per commit `86ff361` (`feat: versioned policy UI`), this page is part of the new versioned policy architecture. Changes to the content or layout must be handled via the `PolicyPageView` logic or the backend-driven versioning system rather than editing this file directly.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
