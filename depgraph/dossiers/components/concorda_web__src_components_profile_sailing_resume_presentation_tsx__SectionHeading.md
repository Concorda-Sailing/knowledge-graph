---
node_id: concorda-web::src/components/profile/sailing-resume-presentation.tsx::SectionHeading
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cab82308a523c26539bee4eb6c01b006afeb30e692c42bddba9561cf2cc136e1
status: current
---

# SectionHeading

## Purpose

The `SectionHeading` component provides a standardized, visually distinct header for the different sections of a user's sailing resume. It is used to group and label data blocks like experience levels, certifications, and race interests. Use this instead of raw `<h2>` tags to ensure consistent typography (uppercase, tracking, and bottom border) across the profile presentation.

## Invariants

- **Visual Style**: Always renders an `<h2>` with `text-[11px]`, `font-semibold`, `uppercase`, and a `border-b` (neutral-300) to maintain the visual hierarchy of the resume.
- **Structure**: Expects `children` as a `React.ReactNode` to allow for text or small inline elements.

## Gotchas

- **Timezone/Date Rendering**: While this is a heading component, the parent `SailingResumePresentation` relies on a specific parsing pattern for `join_date` (slicing the first 4 characters) to avoid the browser-local timezone shifts addressed in commit `f444b4c`. If the heading logic is ever expanded to include date-based text, ensure it follows the pattern of extracting the year from the ISO string rather than using a `Date` object.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Part of the `SailingResumePresentation` which displays user profile data; changes to the visual style here will propagate to all profile views using this presentation component.

## External consumers

None known.
