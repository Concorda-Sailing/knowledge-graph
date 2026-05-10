---
node_id: concorda-web::src/app/members/events/[id]/page.tsx::LegacyEventRedirect
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a3577c05345bdbaf2bb524dfa7ca623f493089a24ffcf629aeff844fcab3f73a
status: current
---

# LegacyEventRedirect

## Purpose

Acts as a compatibility shim for legacy URL structures. It intercepts requests to `/members/events/[id]` and performs a server-side redirect to the current canonical path at `/members/schedule/[id]`. This ensures that older "crew-invite" emails still function without requiring a mass re-send or causing 404 errors for users clicking legacy links.

## Invariants

- **Redirect target is dynamic.** The `id` must be extracted from the `params` promise and appended to the `/members/schedule/` path.
- **Server-side execution.** This is an `async` component that uses `next/navigation`'s `redirect` function, meaning it executes during the server-side rendering/routing phase.

## Gotchas

- **URL structure sensitivity.** Per commit `6638843`, changes to the schedule path or the way `departure_time` and `config` are handled in the destination route can cause unexpected 404s if the redirect target is not perfectly aligned with the new routing logic.

## Cross-cutting concerns

- **Auth**: None. (The redirect happens before any component-level auth checks, but the destination `/members/schedule/[id]` will trigger the standard authenticated route guards).
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Prevents 404 errors in the "crew-invite" email flow.

## External consumers

- Legacy crew-invite emails.
