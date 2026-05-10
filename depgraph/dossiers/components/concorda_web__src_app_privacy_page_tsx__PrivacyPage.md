---
node_id: concorda-web::src/app/privacy/page.tsx::PrivacyPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e991c469b939b0b5ed21d8bb78ea881c5978529a8534d1982f1552d5e8ec5bba
status: current
---

# PrivacyPage

## Purpose

The `PrivacyPage` is a thin routing wrapper that renders the `PolicyPageView` component with a hardcoded `slug`. It serves as the entry point for the privacy policy route, ensuring that the correct policy content is fetched and displayed via the centralized policy view logic.

## Invariants

- **Hardcoded slug**: The component must always pass `slug="privacy_policy"` to `PolicyPageView` to ensure the correct legal document is rendered.
- **Statelessness**: This is a pure routing component; it does not hold local state or manage its own lifecycle beyond the standard React component lifecycle.

## Gotchas

- **Versioned UI requirements**: Per commit `86ff361`, this page is part of a move toward versioned policy UIs. Changes to the policy content or the way the slug is resolved must be handled with awareness of the "versioned policy UI" architecture to avoid breaking the display of legal documents.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
