---
node_id: concorda-web::src/components/boat/boat-profile-tab.tsx::BoatProfileTab
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 959ae4356388d311b74d081d4e88753611f3d2576517e9e202735fc9b1f02f79
status: llm_drafted
---

# BoatProfileTab

## Purpose

A responsive dispatcher component that determines whether to render a full boat profile or a simplified specification view. It acts as a conditional router based on the user's device type and the publication status of the boat's resume. If the user is on a desktop and the resume is published, it renders `BoatProfileCard`; otherwise, it defaults to the `BoatSpecsCard`.

## Invariants

- **Mobile fallback is mandatory.** If `useIsMobile()` returns true, the component always renders `BoatSpecsCard` regardless of the `resume.published` status.
- **Requires a `resume` object or `null`.** The component relies on `resume?.published` to drive the desktop-view logic.
- **Prop-driven rendering.** The component does not manage its own state; it is a pure functional dispatcher based on the `boat` and `resume` props.

## Gotchas

- **Responsive logic is tied to `useIsMobile`.** Because the decision is made during render, a user resizing their browser window from mobile to desktop may see a sudden layout shift from `BoatSpecsCard` to `BoatProfileCard` if the `resume.published` condition is met.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: affects the layout of the boat detail view by switching between a high-density profile and a simplified spec view.

## External consumers

None known.
