---
node_id: concorda-web::src/components/dashboard/profile-completion.tsx::getResumeMissing
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6fbefe6647b2a079dc7b8a0767f1b1c4b4abc6c98c1ba26cfa80e2d2af5ded58
status: llm_drafted
---

# getResumeMissing

## Purpose

Calculates the list of missing fields for a user's `SailingResume` to drive the "Profile Completion" UI. It identifies which core attributes (About me, Experience level, Preferred roles) are empty or unpopulated. This is distinct from `getPrefsMissing` or `getBoatMissing`, which handle availability and vessel-specific data respectively.

## Invariants

- **Input is `SailingResume | null`**: If the resume is null, it returns a hardcoded set of three missing fields: `["About me", "Experience level", "Preferred roles"]`.
- **Returns `string[]`**: The output is a list of human-readable strings used for display in the dashboard progress indicator.
- **`positions_preferred` check**: A resume is only considered complete regarding roles if the `positions_preferred` array has a non-zero length.

## Gotchas

- **Implicit "Published" state**: The function is used to determine if a user is "ready" for Crew Finder. If `isPublished` is false, the UI displays "Not yet published" regardless of the actual content of the resume.
- **Dependency on `SailingResume` structure**: Changes to the `SailingResume` type (e.g., renaming `about_me` or `experience_level`) will break the logic here, as it relies on truthiness of these specific fields.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Drives the visibility of the "Profile Completion" status in the user dashboard.

## External consumers

None known.
