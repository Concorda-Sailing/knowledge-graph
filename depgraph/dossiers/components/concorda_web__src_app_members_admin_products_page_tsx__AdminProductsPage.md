---
node_id: concorda-web::src/app/members/admin/products/page.tsx::AdminProductsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a5ed92634a75cf7c1e402ac081f5f5628f21e3099c40a035d6b92c9a751b446
status: current
---

# AdminProductsPage

## Purpose

This component serves as a legacy redirector for the `/members/admin/products` route. It immediately redirects any incoming request to the more specific `/members/admin/products/memberships` path to ensure users are routed to the correct sub-resource.

## Invariants

- **Immediate Redirect**: The component must always execute a `redirect("/members/admin/products/memberships")`.
- **Server-side execution**: As a Next.js App Router page component, the redirect occurs during the initial request/render phase.

## Gotchas

- **Route Deprecation**: Per commit `fbb3579`, this page is no longer a standalone destination but a redirector. Any logic intended for "Products" must now be implemented in the `[category]` sub-routes (e.g., `CategoryProductsPage`) to avoid being caught by this redirect.

## Cross-cutting concerns

- **Auth**: Relies on the implicit middleware/layout protection for the `/members/admin/` path.
- **Side effects**: Redirects users away from the root products path to the memberships sub-route.

## External consumers

None known.
