---
node_id: concorda-web::src/components/profile/privacy-form.tsx::PrivacyForm
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c938b0bbb2974564c2ea779a4bdc2050e96e69c67bac5c11c6adb078887a49af
status: llm_drafted
---

# PrivacyForm

## Purpose

The `PrivacyForm` component provides a UI for users to manage their email subscription preferences (mailing list opt-in status). It is a specialized sub-form within the profile section that handles the transformation of a simple boolean toggle into the nested `ProfileUpdate` structure required by the API. Use this when you need to allow a user to toggle their subscription status without exposing the full profile object to the client-side state.

## Invariants

- **Input is a `Profile` object.** It extracts the current state from `profile.preferences.mailing_list.opt_in`.
- **Output via `onUpdate` is a full `Profile` object.** The component must pass the updated profile back to the parent to ensure the UI remains in sync with the server.
- **`handleSubmit` creates a nested `ProfileUpdate` object.** It explicitly sets `event_notices: true` and `general_news: true` alongside the `mailing_list.opt_in` value to satisfy the API's expected shape for preference updates.
- **Success state is ephemeral.** The success message is hardcoded to disappear after 3000ms via `setTimeout`.

## Gotchas

- **Strict nesting requirement.** Per commit `6607a79`, the update must follow a specific nested structure (`preferences.mailing_list.opt_in`) to avoid type errors and ensure the backend accepts the payload.
- **Manual `initialRef` sync.** The component uses `initialRef.current = { ...formData }` to track the "dirty" state relative to the last successful save. If this sync is broken, the `isDirty` check (which relies on `JSON.stringify`) will produce incorrect results.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi.update`, which requires a valid authenticated session (managed by the parent component/route).
- **Side effects**: Triggers a refresh of the user's profile data via the `onUpdate` callback, which likely updates the global user context or profile display in the header/dashboard.

## External consumers

None known.
