---
node_id: concorda-web::src/app/members/courses/page.tsx::CoursesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0d625c755565061abba9e90cfd4652d2f8e873e5523455f1cc8083517c0cbfad
status: current
---

# CoursesPage

## Purpose

The static informational page for "Standard Courses" within the member yearbook. It provides visual and textual context regarding course letters, compass bearings, and distance to Mark 1. This is a purely presentational component used to educate members on race committee signaling and GSI (General Sailing Instructions) rules.

## Invariants

- **Static Content**: The page relies on a local image asset `/courses.png` to display the course layout.
- **Unoptimized Image**: The `Image` component uses the `unoptimized` prop and `priority` to ensure the course diagram loads immediately without Next.js image optimization overhead, as it is a static asset.
- **Layout**: The component is wrapped in a `Card` and `CardContent` to maintain visual consistency with other yearbook pages.

## Gotchas

- **Static Asset Dependency**: The component is hard-coded to `/courses.png`. If the image is moved or renamed in the `public/` directory, this page will render a broken image.
- **Content is not dynamic**: Unlike other pages in the `members/` directory, this does not fetch from an API; it is a hard-coded informational view.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
