---
node_id: concorda-web::src/components/profile/sailing-resume-presentation.tsx::SailingResumePresentation
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2fc1cfd605862f76e1037862ee155d92c5c762e2d50277d7faa448c83180b26d
status: llm_drafted
---

# SailingResumePresentation

## Purpose

Renders a highly structured, print-optimized view of a user's sailing profile. It transforms raw data (like `experience_level` and `certifications`) into human-readable labels using `useConstants` and `titleCase`. This component is specifically designed to be used with a `printRef` for generating physical or PDF resumes, ensuring that layout-critical elements like the "About" section use `break-inside-avoid`.

## Invariants

- **Input relies on `profile` and `resume` objects.** The component expects a `profile` with at least a `join_date` and a `resume` object containing sailing-specific metadata.
- **`joinYear` is derived via string slicing.** It extracts the first 4 characters of the `profile.join_date` string to avoid browser-local `Date` object shifts.
- **Labels are derived from constants.** Values like `experience_level` and `certifications` are mapped against `useConstants()` to ensure the UI displays human-readable labels rather than raw database keys.
- **Layout is print-aware.** Uses `break-inside-avoid` on sections to prevent awkward page breaks in PDF/print-outs.

## Gotchas

- **Avoid `new Date()` for the join year.** Per commit `f444b4c`, the component must parse the year directly from the `join_date` string (e.g., `slice(0, 4)`) to prevent timezone-induced shifts that could incorrectly display the wrong year in non-ET browsers.
- **`titleCase` is the fallback.** If a value (like `boat_classes_sailed`) does not exist in the constants, the component falls back to `titleCase(c)` to ensure the UI doesn't show raw snake_case strings.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: This component is the primary visual output for the "Sailing Resume" feature; changes to the layout will affect the visual quality of printed/PDF versions of user profiles.

## External consumers

None known.
