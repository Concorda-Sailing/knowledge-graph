---
node_id: concorda-web::src/lib/content.ts::readContent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5b19358492852cf9a5e930cb4a417ccfc1beb4f7b7a37bb6f635d6771b76407d
status: llm_drafted
---

# readContent

## Purpose
Synchronous Node-side helper that reads a markdown file from `src/content/<slug>.md` and returns its raw contents as a UTF-8 string. Exists so static-ish info pages (yearbook content like awards, fleets, marks, rules, scoring) can author copy in plain markdown checked into the repo, then render it through Next.js server components without going through the API or DB. Treat it as a build/render-time file read, not a runtime data source — it must only be called from server components or other server-only contexts.

## Invariants
- Always called from a server component / server-only path; bundling this into a client component would either error at build time (no `node:fs`) or ship `fs` shims. The five current callers are all `app/members/*/page.tsx` server components.
- The slug must correspond to an actual `src/content/<slug>.md` file checked into the repo at build time. There is no fallback, no existence check, and no try/catch — a missing file throws `ENOENT` and the page 500s.
- Path is resolved from `process.cwd()`, which on Next.js means the project root. Relies on the dev server and the production build both being launched from the repo root; running from a subdirectory breaks it.
- Returns the raw markdown including any leading H1. Pages that render their own title via `YearbookHeader` are expected to pipe through `stripLeadingH1` first; new content pages should follow that convention to avoid double titles.

## Gotchas
- `slug` is interpolated directly into the path. Nothing sanitizes `..` or absolute paths — fine today because all callers pass hardcoded literal strings, but if a slug ever comes from user input or a route param this becomes a path-traversal read primitive. Keep slugs as inlined string literals.
- Synchronous `readFileSync` blocks the request thread. Acceptable for tiny static markdown but don't repurpose this for large or numerous files; switch to `fs/promises` if the caller pattern changes.
- Only one commit in history (`d647124`, the yearbook content pages introduction) — no battle scars yet, but also no settled conventions beyond what those five pages established.

## Cross-cutting concerns
- No auth, no rate limit, no audit, no websocket — pure local file I/O. The pages that call it sit under `app/members/`, so route-level auth on the parent layout is what gates access; this helper trusts that and adds nothing of its own.
- Side effect: ties deployed bundles to repo content. Editing a `.md` under `src/content/` requires a redeploy to take effect — content is not hot-reloadable via the admin UI or any CMS path.

## External consumers
None known. Internal Next.js server components only; not exposed via API, not consumed by the Expo app, not called by any scheduled job.

## Open questions
- Should this migrate to `fs/promises` + `async` for consistency with the rest of the server-side code? Probably premature given five callers and trivial file sizes.
- Is `src/content/` the right long-term home, or should yearbook copy eventually live in the database so non-developers can edit it? Out of scope for this helper, but the answer determines whether `readContent` survives or gets replaced by an API call.
