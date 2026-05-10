---
node_id: concorda-web::src/components/profile/sections/sailing-experience-section.tsx::SailingExperienceSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0e4252b50f6379bc8ce21f42854041378e5ccf9245aadeca7d0f752b8fcc08d3
status: current
---

# SailingExperienceSection

## Purpose

Displays and manages the user's sailing resume data, including a high-level overview and a detailed form for editing. It acts as a container for both `SailingResumePresentation` (read-only view) and `SailingResumeForm` (edit mode), toggled via the `useInlineEdit` hook. Use this component when you need to provide a sectioned, editable profile area that supports both PDF generation and inline state updates.

## Invariants

- **Requires `profile` and `resume` props.** The `profile` provides the name for filename generation, while `resume` contains the actual sailing data.
- **`onResumeUpdate` is the single source of truth for updates.** All changes from the internal form must be bubbled up via this callback to ensure the parent state remains synchronized.
- **PDF generation relies on `printRef`.** The `onDownloadPdf` function uses `html2pdf.js` to capture the `printRef` element; if the ref is not attached to the presentation component, the download will fail.
- **`missing` count is derived from specific fields.** It tracks the presence of `about_me`, `experience_level`, and `positions_preferred` to alert the user to incomplete profile data.

## Gotchas

- **PDF generation is an async side-effect.** The `onDownloadPdf` function uses a dynamic import for `html2pdf.js` to keep the initial bundle size down, but this can cause a
