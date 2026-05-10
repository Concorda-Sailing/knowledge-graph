---
node_id: concorda-web::src/app/events/[slug]/page.tsx::renderMarkdown
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e37e617e9230e7d83f37ec8ab1bd7c941b5985bc241a41b935c86440df4b945e
status: current
---

# renderMarkdown

## Purpose

A lightweight Markdown-to-HTML parser used to render event descriptions and text fields. It converts basic Markdown syntax (bold, italics, links, and bulleted lists) into HTML strings for safe rendering within the `PublicEventPage`. It is a local utility and is not intended to support complex Markdown features like images or nested-list structures.

## Invariants

- **Input is a raw string.** The function expects a plain text string containing Markdown-like syntax.
- **Output is an HTML string.** The returned string is designed to be injected into a component (likely via `dangerouslySetInnerHTML` or a similar mechanism).
- **Supports basic syntax only.** It specifically handles `**bold**`, `_italics_`, `[text](url)`, and `- list items`.
- **Line breaks are converted to `<br />`.** Every newline in the input string results in a break tag in the output.

## Gotchas

- **Manual list handling.** The function checks `if (html.startsWith("- "))` to wrap list items in a `<li>` tag with a specific class (`ml-4 list-disc`). This means it does not support nested lists or any other bullet types (e.g., `*` or `+`) without manual adjustment.
- **Regex-based replacement.** Because it uses global regex replacements for bold and italics, highly complex or malformed Markdown might result in unexpected HTML nesting.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
