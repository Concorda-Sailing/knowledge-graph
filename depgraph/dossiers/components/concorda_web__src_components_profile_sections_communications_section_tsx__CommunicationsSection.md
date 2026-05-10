---
node_id: concorda-web::src/components/profile/sections/communications-section.tsx::CommunicationsSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bf92bf77f201b055e4e1742e05382da87691104ce1981f07e881c71c99be9dc9
status: current
---

# CommunicationsSection

## Purpose

The `CommunicationsSection` provides a UI for users to view and edit their mailing list preferences. It manages the transition between a read-only state (displaying the current subscription status) and an editable state via the `useInlineEdit` hook. It is distinct from `SecuritySection` or `SailingExperienceSection` by focusing exclusively on the `profile.preferences.mailing_list` data structure.

## Invariants

- **Uses `useInlineEdit("communications")`** to manage the local editing state and lifecycle.
- **Requires a `profile` object of type `Profile`** to display the current `mailing_list.opt_in` status.
- **The `onProfileUpdate` callback must be invoked** to persist changes back to the parent state/server after a successful save.
- **The `CommunicationsForm` is passed a `ref`** via `registerForm("communications")` to allow the hook to manage form registration and dirty state.

## Gotchas

- **Extracted component logic**: Per commit `98e4071`, this section was recently extracted from a larger profile component. Ensure that any logic previously handled by the parent profile view that relies on the "communications" key is now correctly handled by the `useInlineEdit` hook.

## Cross-cutting concerns

- **Auth**: Requires an authenticated user session to successfully trigger `onProfileUpdate` via the underlying API.
- **Side effects**: Updates to this section trigger the `onProfileUpdate` callback, which typically refreshes the user's profile data in the parent `ProfilePage` component.

## External consumers

None known.
