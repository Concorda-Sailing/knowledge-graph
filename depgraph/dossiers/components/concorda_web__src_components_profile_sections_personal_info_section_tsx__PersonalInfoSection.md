---
node_id: concorda-web::src/components/profile/sections/personal-info-section.tsx::PersonalInfoSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cd940bad3aa4cb0f73bf17d7de71536fcb0240740eaab70c4e9dc769b7378280
status: current
---

# PersonalInfoSection

## Purpose

Displays and manages the user's core identity data (name, email, phone, DOB, and club affiliations). It acts as a wrapper for `ProfileForm` when in edit mode, using the `useInlineEdit` hook to toggle between a read-only view and an editable form. Use this component for high-level identity display; use `ProfileForm` directly if you need to implement a different editing pattern or a more granular form.

## Invariants

- **Uses `useInlineEdit("personal")`** to manage the local editing state and registration of the form ref.
- **Requires a `profile` object of type `Profile`** to render any data.
- **Displays a `Badge` if `profile.phone_number` is missing**, serving as a visual indicator for incomplete profiles.
- **The `onProfileUpdate` callback** must be provided to handle the successful submission of the `ProfileForm`.

## Gotchas

- **Single-column reflow requirement:** Per commit `24dd505`, this component was recently refactored to use a single-column layout for better responsiveness in the profile view. Ensure any layout changes maintain this vertical stacking behavior for mobile compatibility.

## Cross-cutting concerns

- **Auth**: Requires an authenticated user session to view/edit, as it relies on the `Profile` type and `onProfileUpdate` logic.
- **Side effects**: Updates to this section trigger a re-render of the parent profile view via `onProfileUpdate`.

## External consumers

None known.
