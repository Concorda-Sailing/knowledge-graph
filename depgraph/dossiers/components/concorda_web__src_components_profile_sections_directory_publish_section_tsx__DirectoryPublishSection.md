---
node_id: concorda-web::src/components/profile/sections/directory-publish-section.tsx::DirectoryPublishSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 887aae3a7f741b92ecc1f278494376d7012d8dd249db36fa3efe288617836b0d
status: llm_drafted
---

# DirectoryPublishSection

## Purpose

A UI wrapper for the member directory visibility controls. It provides a visual container (Card) for the `DirectoryPublishBar` and serves as a structural section within the user profile page. It is distinct from `CrewfinderOptinSection` (its sibling in the same directory), which handles visibility for recruitment-specific flows rather than general directory presence.

## Invariants

- **Requires a `Profile` object.** The component expects a valid profile instance to pass down to the internal bar.
- **Uses `DirectoryPublishBar` for logic.** This component is purely a layout wrapper; all state management and API calls for publishing status are handled by the child component.
- **Prop drilling pattern.** It passes `onProfileUpdate` directly through to the child to ensure the parent profile state stays in sync after a change.

## Gotchas

- **Extracted component logic.** Per commit `9f71a80`, this was recently extracted from a larger profile component to isolate the directory visibility logic. If you are looking for the actual toggle logic or API call, do not look here; look at `DirectoryPublishBar`.

## Cross-cutting concerns

- **Auth**: None (relies on the parent profile component's authentication context).
- **Side effects**: Updates to the profile visibility status via `onProfileUpdate` will affect the user's visibility in the global member directory.

## External consumers

None known.
