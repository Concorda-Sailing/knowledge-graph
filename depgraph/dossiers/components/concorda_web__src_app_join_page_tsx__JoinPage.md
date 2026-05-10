---
node_id: concorda-web::src/app/join/page.tsx::JoinPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 78e78317f885a7e20e031923236d27e8d1109454b38689a44ed8b0c4a4204f85
status: llm_drafted
---

# JoinPage

## Purpose

The landing page for the application, serving as the public-facing marketing and onboarding entry point. It displays the organization's branding, a hero section, and a dynamic list of available membership/product options fetched from the API. It is designed to provide a high-level overview of what the organization offers before a user authenticates.

## Invariants

- **Fetches via `temporalProductsApi.getAvailable()`** — The page relies on this specific API call to populate the membership cards.
- **Filters for "Membership" category** — The `memberships` state only includes products where `p.category === "Membership"`.
- **Displays a loading state** — Uses the `Skeleton` component from the UI library while `membershipsLoading` is true to prevent layout shift.
- **Uses `useConstants()` for branding** — The `orgName` and `OrgBrand` are derived from the global organization context to ensure brand consistency.

## Gotchas

- **Hardcoded Hero Text** — The hero section contains specific copy for "Massachusetts Bay Sailing Association" (line 120). If the organization name changes in `useConstants`, this text will be out of sync with the brand component.
- **Category Filtering** — Because the component explicitly filters for `p.category === "Membership"` (line 81), any new product types added to the API (e.g., "Donations" or "Event Passes") will not appear on this page unless the filter is updated.
- **Image Path Dependency** — The hero image is a static asset at `/hero-sailing-2.jpg`. If this file is moved or renamed in the public directory, the hero section will render a broken image.

## Cross-cutting concerns

- **Auth**: None. This is a public-facing page.
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: None.

## External consumers

None known.
