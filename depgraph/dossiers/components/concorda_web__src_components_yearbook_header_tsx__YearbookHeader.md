---
node_id: concorda-web::src/components/yearbook-header.tsx::YearbookHeader
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d7300ba5d307e4ed26c70c7a74cb5e7c1751562b74287cb0b020e44a09f91861
status: llm_drafted
---

# YearbookHeader

## Purpose

The `YearbookHeader` provides a standardized, high-contrast navy header band for the racing and yearbook-related pages (Awards, Fleets, Rules, Scoring, Marks). It is designed to mirror the visual branding of downloadable PDFs, ensuring a consistent identity across the web app and physical documents. It is a purely presentational component that accepts a `title`, an optional `subtitle`, and an optional `actions` slot for buttons or controls.

## Invariants

- **Uses `useConstants()` for branding.** The component must pull `logoUrl` and `orgName` from the global constants to ensure the MBSA logo and organization name are consistent with the current context.
- **Implements `unoptimized` Image.** The internal `Image` component uses the `unoptimized` prop to prevent unnecessary processing of the organization's logo.
- **Layout is responsive but constrained.** The title and subtitle use `truncate` to prevent text overflow from breaking the header layout on smaller viewports.
- **Visual hierarchy is fixed.** The component is hardcoded with a `bg-primary` background and `text-primary-foreground` to maintain the "navy bar" aesthetic.

## Gotchas

- **Negative margins for full-bleed look.** The component uses `-mx-6 -mt-6` to offset the container's padding, ensuring the navy band stretches to the edges of the parent container's layout.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
