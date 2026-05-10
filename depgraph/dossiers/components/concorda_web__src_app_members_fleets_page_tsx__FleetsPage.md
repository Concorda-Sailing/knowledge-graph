---
node_id: concorda-web::src/app/members/fleets/page.tsx::FleetsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 40c09c3272ce1dbaa7d08b31ad13ab19a646375c5395ad3ab648077f151ad99c
status: current
---

# FleetsPage

## Purpose

The `FleetsPage` component renders the static documentation for MBSA Class Splits and Fleet Structure. It serves as a specialized content view that pulls raw markdown from the `fleets` content key, strips the leading H1 via `stripLeadingH1`, and renders the result using the standard `Markdown` component. This is a static-content-driven page rather than a data-driven dashboard.

## Invariants

- **Content source is external to the component.** The text is fetched via `readContent("fleets")`, meaning the visual output is controlled by the content files in the `lib/content` directory, not by component state.
- **Uses `YearbookHeader` for consistent branding.** The page must maintain the `title="Fleets"` and `subtitle="MBSA Class Splits & Fleet Structure"` structure to match the yearbook-style layout used across the member portal.
- **Requires `stripLeadingH1` for valid rendering.** The `Markdown` component expects content without a redundant top-level heading to prevent double-rendering of the title.

## Gotchas

- **Content-driven layout.** Per commit `d647124`, this page is part of the "yearbook content pages" initiative. Changes to the visual structure of the page are driven by the markdown content and the `stripLeadingH1` utility rather than code changes to the component itself.

## Cross-cutting concerns

- **Auth**: None (Content is rendered via `readContent`, which is a local file-system/build-time utility).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
