---
node_id: concorda-web::src/app/events/[slug]/page.tsx::renderLocation
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 54570181b12e751b58fd38a4ac1c920f43514aae87da86de83712a23d9ceffc9
status: current
---

# renderLocation

## Purpose

The `renderLocation` helper transforms a plain string into a React fragment containing clickable hyperlinks. It uses a regex to identify URLs within the string and wraps them in an `<a>` tag with `target="_blank"` and `rel="noopener noreferrer"`. This allows event locations (like addresses or website links) to be interactive without requiring a full markdown parser for the entire location field.

## Invariants

- **Input is a string.** The function expects a single string representing a location.
- **Regex pattern is global.** It uses `/(https?:\/\/[^\s)]+)/g` to ensure multiple URLs in a single string are all captured and rendered.
- **Links are non-blocking.** The `onClick` handler calls `e.stopPropagation()` to ensure clicking a link doesn't trigger any parent container click events.
- **Security/UX.** All generated links must include `rel="noopener noreferrer"` to prevent tab-nabbing and ensure safe cross-origin navigation.

## Gotchas

- **Regex-based parsing is brittle.** The pattern `[^\s)]+` assumes URLs are delimited by whitespace or a closing parenthesis. If a URL is followed by other punctuation (like a period or comma) without a space, the punctuation may be swallowed into the URL or break the link.
- **Manual HTML injection via `renderMarkdown`.** While `renderLocation` is a simple regex helper, the sibling `renderMarkdown` (lines 82-98) performs manual string replacement for `<strong>` and `<em>` tags. If a developer attempts to use `renderMarkdown` logic inside `renderLocation`, they may introduce XSS vulnerabilities or broken layouts.

## Cross-cutting concerns

- **Auth**: none.
- **Websocket**: none.
- **Audit**: N.
- **Rate limit**: none.
- **Side effects**: none.

## External consumers

None known.
