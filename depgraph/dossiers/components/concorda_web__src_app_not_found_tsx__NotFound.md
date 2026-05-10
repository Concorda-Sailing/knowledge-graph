---
node_id: concorda-web::src/app/not-found.tsx::NotFound
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 33d7a28c317511ed2e31aceeaae310a84e0f7c0088209c56d367f8b20d7d1fc9
status: llm_drafted
---

# NotFound

## Purpose

The fallback UI component rendered by Next.js when a route is not matched or a `notFound()` call is triggered. It provides a standardized "404" interface with a link back to the root path to prevent users from being stuck on a dead end.

## Invariants

- **Static rendering is safe.** The component contains no dynamic data fetching or client-side state, making it safe for static generation.
- **Uses standard Tailwind classes.** Layout relies on `flex`, `items-center`, and `justify-center` to ensure the error message is centered regardless of viewport size.
- **Returns a single `Link` to `/`.** The primary navigation path is hardcoded to the root directory.

## Gotchas

- **Next.js 16/React 19 compatibility.** Per commit `39009cf`, this file was part of the upgrade path to Next.js 16 and React 19; ensure any future styling changes do not introduce incompatible React 19 patterns or breaking changes to the `Link` component behavior.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
