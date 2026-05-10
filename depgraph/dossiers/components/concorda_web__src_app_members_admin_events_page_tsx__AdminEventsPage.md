---
node_id: concorda-web::src/app/members/admin/events/page.tsx::AdminEventsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0f35b04e2358450b69be8213eff6dc32cc02c04bf0f3f1b6e8df9e16b3f49392
status: llm_drafted
---

# AdminEventsPage

## Purpose

Acts as a routing redirector for the admin events section. Instead of hosting a view, it immediately redirects users to the specific sub-route for races. This ensures that any legacy or direct hits to the base `/members/admin/events` path are funneled into the correct sub-categorized view.

## Invariants

- **Always performs a redirect.** The component is a functional stub that calls `redirect("/members/admin/events/races")`.
- **Must remain a server-side redirect.** It uses `next/navigation` to ensure the client is moved to the sub-route before any heavy component tree is mounted.

## Gotchas

- **The page is no longer a container.** Per commit `bb1c40f` ("Split admin Events page into Regattas and Socials tabs"), this page was stripped of its UI to serve as a redirector. Do not attempt to add UI or sub-navigation logic here; the actual content lives in the sub-routes (e.g., `/races` or `/socials`).

## Cross-cutting concerns

- **Auth**: Relies on the implicit admin guard of the parent layout/route group.
- **Side effects**: Redirects users to the race-specific view, which is the primary entry point for the "sailing calendar" and "crew management" features mentioned in commit `76ad44e`.

## External consumers

None known.
