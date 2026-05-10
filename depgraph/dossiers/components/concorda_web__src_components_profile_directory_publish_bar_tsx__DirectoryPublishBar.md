---
node_id: concorda-web::src/components/profile/directory-publish-bar.tsx::DirectoryPublishBar
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 420746566ba8279c15e67e82ac057904c53001c689a1c1d2b06d2b4758d49eaa
status: llm_drafted
---

# DirectoryPublishBar

## Purpose

A UI component that manages a user's visibility settings within the member directory. It provides a toggle for the overall "opt-in" status and individual checkboxes for name, phone, and email visibility. It is distinct from `CrewfinderPublishBar` in that it specifically manages the `directory` preference object via `profileApi.update`.

## Invariants

- **`opt_in` is a derived state.** If any individual visibility checkbox (name, phone, or email) is checked, `opt_in` must automatically become `true`.
- **`opt_in` can only be disabled if all sub-fields are unchecked.** If a user unchecks all individual fields, the component must set `opt_in` to `false`.
- **`profileApi.update` payload structure.** The component must wrap the `formData` inside a `preferences.directory` object to match the expected API schema.
- **`onUpdate`-driven state sync.** Upon a successful API call, the component calls `onUpdate(updated)` to ensure the parent component's state reflects the new server-side truth.

## Gotchas

- **Auto-enable logic (commit `8b9f474`).** Previously, users could not easily turn on visibility if the toggle was off. The current implementation ensures that checking a box (like `show_name`) automatically sets `opt_in` to `true`.
- **Toggle-off behavior (commit `8b9f474`).** If the user toggles the main switch to "off", the component must explicitly set `opt_in: false` regardless of the state of the individual checkboxes.
- **Manual revert on failure.** The `handleSubmit` function catches errors but currently lacks a robust rollback mechanism for the local `formData` state if the `profileApi.update` call fails.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to call `profileApi.update`.
- **Side effects**: Successful updates trigger `onUpdate`, which typically refreshes the user's profile view in the parent component.

## External consumers

None known.
