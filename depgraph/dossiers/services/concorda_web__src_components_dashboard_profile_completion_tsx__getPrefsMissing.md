---
node_id: concorda-web::src/components/dashboard/profile-completion.tsx::getPrefsMissing
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c7a70e8e60feb321c74c3e12e7d9ed593e5a02d35d6ae27716b09d6c3903445d
status: current
---

# getPrefsMissing

## Purpose

Identifies missing fields in a user's sailing preferences to drive the onboarding/setup wizard. It calculates which specific data points (Race areas or Available days) are absent from the `SailingResume` object. This is distinct from `getResumeMissing`, which focuses on biographical data, and `getBoatMissing`, which focuses on vessel details.

## Invariants

- **Input is `SailingResume | null`**. If the resume is null, it defaults to returning `["Race areas", "Available days"]`.
- **"Available days" is a composite check**. A user is only considered to have "missing" availability if *all* day properties (Monday through Sunday) are falsy.
- **Returns a `string[]` of human-readable labels**. These strings are used directly in the UI to prompt the user for missing information.

## Gotchas

- **The "Available days" check is an "all-or-nothing" logic**. Per the implementation of `hasDay`, if a user has even one day (e.g., `monday: true`), the function considers the availability requirement met. This might be too permissive if the goal is to ensure a diverse range of availability.
- **Dependency on `SailingResume` structure**. The function relies on the existence of `resume.availability` and its sub-properties. If the API response for `SailingResume` changes to use a different nesting pattern for availability, this will return incorrect "missing" states.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Drives the visibility of the setup wizard/onboarding progress in the dashboard.

## External consumers

None known.
