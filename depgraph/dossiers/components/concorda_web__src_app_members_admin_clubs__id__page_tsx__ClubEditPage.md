---
node_id: concorda-web::src/app/members/admin/clubs/[id]/page.tsx::ClubEditPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c97a73b9a247800e572d1c2d85b8685c162ad6765038fbc4a385e4c61f719f77
status: llm_drafted
---

# ClubEditPage

## Purpose

The administrative interface for editing organization (Club) details, including core identity, contact information, and social media presence. It manages a complex local state for both the organization's profile and its associated contacts. Use this component when you need to modify the high-level metadata of a club or manage the `OrgContact[]` list.

## Invariants

- **State synchronization**: The `form` state is initialized by mapping properties from the `org` object returned by `organizationsApi.get(clubId)`.
- **Contact separation**: Contact data is fetched via a separate `orgContactsApi.list(clubId)` call to ensure the organization profile and its personnel are treated as distinct entities.
- **Role mapping**: The `ROLE_LABELS` constant defines the human-readable strings for the `role` field in the contact form (e.g., `delegate`, `billing`, `fleet_captain`, `rc_chair`).
- **Address nesting**: The form flattens the `address` object from the API (street, city, state, zip) into a flat `form` state for easier editing.

## Gotchas

- **Generalization of "Clubs"**: Per commit `31d8b03`, this page was recently generalized to handle all organization types, not just traditional "Clubs." Ensure any logic added here respects the broader `Organization` type rather than assuming a specific nautical structure.
- **Mobile Layout Reflow**: Per commit `019f6e3`, admin sub-directory tables and forms are subject to a single-column reflow on mobile. Changes to the form layout must be tested against the mobile-first layout pattern established in that commit.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges to access the `[id]` route and execute `organizationsApi` calls.
- **Side effects**: Updates to this page (via `organizationsApi`) will affect the visibility of the organization's name, abbreviation, and contact details across the platform, including the "Club filter" mentioned in commit `5015da5`.

## External consumers

None known.

## Open questions

- The `vhf_channel` is cast to a `String` during the `loadClub` mapping. If the API returns a numeric type, this prevents runtime errors, but we should confirm if a specific format is required for the input field.
