---
node_id: concorda-web::src/lib/content.ts::stripLeadingH1
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 77c1b9ac8874d1d203aa275fb5697b467ad96e81fae5a7936b29617af72e6ca9
status: llm_drafted
---

# stripLeadingH1

## Purpose
Frontend helper that strips a leading H1 (`# Title\n`) from a markdown string before it is rendered. Pairs with `readContent` in the same file: yearbook-style member pages (`awards`, `fleets`, `marks`, `rules`, `scoring`) read a `.md` file from `src/content/`, render the title themselves via `<YearbookHeader title=... />`, and pass the body through `stripLeadingH1` so the on-page title and the markdown's own `# Heading` don't visually duplicate. If a future page wants the markdown's H1 to render, it should call `readContent` directly and skip this helper.

## Invariants
- The regex is anchored with `^` and only removes the *first* H1 — subsequent `#` headings in the body must survive untouched.
- Only matches ATX H1 (`# `, one or more spaces). Setext H1 (`Title\n====`) and `#` without a trailing space are intentionally not stripped.
- Requires at least one trailing newline (`\n+`); a markdown string consisting solely of `# Title` with no newline is returned unchanged. All current `src/content/*.md` files have trailing newlines.
- Pure string in / string out, no I/O — safe to call in server components and during SSG.

## Gotchas
- Single commit in history (`d647124 feat(racing): yearbook content pages…`) — no reverts or fixes yet, so the bite-list is theoretical. The likely future bite: someone adds a content file whose first line is *not* an H1 (e.g. a frontmatter block, a paragraph, or `## Subhead`), in which case the function is a no-op and the page renders without a title-strip — usually fine, but easy to misread as a bug.
- Callers in `awards/page.tsx` split the file on `^---$` first and only strip the H1 from the *intro* half; the honoraria half is rendered as-is. If you change the regex, re-check that page — it's the only multi-section consumer.
- Regex does not handle `\r\n` line endings explicitly. `.+` is greedy but does not cross newlines, so `\r` would be captured into the title and `\n+` would still match — probably fine on Unix-authored content, untested on CRLF.

## Cross-cutting concerns
None. No auth, no network, no audit, no websocket. Runs at request/build time inside Next.js server components alongside `readContent`. Side effect surface is purely visual (rendered HTML).

## External consumers
None known. Internal to the web app's yearbook member pages.

## Open questions
- Should this also strip a trailing blank line / surrounding whitespace, or is the current "first H1 + immediate newlines" contract enough? Current behavior leaves any leading whitespace before the `#` intact, which would skip the strip — no caller hits that today.
