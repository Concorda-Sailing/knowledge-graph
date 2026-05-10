---
node_id: concorda-test::tests/boats/boat-resume.spec.ts::test@25
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 19e8b2ace287336ada5d4cadf6e1a317898b20551e58579c4dd0dce350041e78
status: current
---

# boat profile section is accessible from Overview

## Purpose

Verifies the accessibility and editability of the boat profile section within the Overview tab. It ensures that the "Profile" section (formerly a standalone tab) is visible, that the `BoatResumeView` displays the correct seeded data, and that the `BoatResumeForm` allows for updating the "about" field and toggling visibility.

## Invariants

- **The "Profile" section is a Card within the Overview tab**, not a standalone tab.
- **The `editBtn` is a button with the name `/edit profile/i`** and serves as the trigger to switch from `BoatResumeView` to `BoatResumeForm`.
- **The "about" field is a `textarea` with `id="about"`**.
- **Saving requires an explicit click on a button with the text `/^save$/i`**.
- **The test must be idempotent** by reverting the "about" field value to its original state after the edit test completes.

## Gotchas

- **Selector changes due to UI consolidation**: Per commit `ba1c3bd`, the "Profile" tab was consolidated into the Overview tab; tests must now locate the profile section via the `CardTitle` or the presence of the edit button rather than a top-level navigation link.
- **Navigation path change**: Per commit `6a1bf88`, the navigation to the boat resume was updated to use the `Boats` panel instead of the removed per-boat tab.
- **Form submission method**: Per commit `39a9fea`, the `about` field can be submitted via the `Enter` key, but the E2E test relies on the explicit `Save` button to ensure the form-specific save logic is triggered.
- **Wait for network idle**: Because switching to/from edit mode involves a state change in the UI, `page.waitForLoadState('networkidle')` is required after clicking the edit button to prevent race conditions with the form rendering.

## Cross-cutting concerns

- **Auth**: Requires authenticated session (assumed via `boat-crud.spec.ts` patterns) to access the boat detail page.
- **Side effects**: Updating the "about" field or the publish toggle affects the visibility of the boat's details in the global boat-finder/search views.

## External consumers

None known.
