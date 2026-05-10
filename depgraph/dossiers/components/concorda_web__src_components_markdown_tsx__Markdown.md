---
node_id: concorda-web::src/components/markdown.tsx::Markdown
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 29c12ee82fe4499568f0a823aabf7e26ae34d7a72fcc5e2d3db077863d72e5ed
status: current
---

# Markdown

## Purpose

A specialized wrapper around `react-markdown` used to render Markdown-formatted strings with consistent styling across the web application. It provides a standardized set of Tailwind CSS classes for HTML elements (headings, lists, tables, etc.) to ensure that user-generated or system-generated content matches the design system's typography and spacing. Use this instead of raw `react-markdown` to maintain visual consistency in areas like the Yearbook or Profile sections.

## Invariants

- **Input must be a string.** The `content` prop is a single string containing raw Markdown.
- **Includes GFM support.** The component automatically applies `remarkGfm` to ensure tables and task lists render correctly.
- **Styling is opinionated.** Elements like `h1` through `h4` and `blockquote` have hardcoded Tailwind classes for margins, font weights, and colors.
- **Links are secure.** All `<a>` tags are automatically assigned `target="_blank"` and `rel="noreferrer noopener"`.

## Gotchas

- **Styling is fixed for specific elements.** Because classes like `text-primary` and `text-foreground/90` are hardcoded into the component mapping, any attempt to pass custom styles via props to the underlying HTML elements will be overridden by the internal component definitions.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: None known.

## External consumers

None known.
