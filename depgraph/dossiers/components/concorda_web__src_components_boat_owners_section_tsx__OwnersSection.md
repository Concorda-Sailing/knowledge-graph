---
node_id: concorda-web::src/components/boat/owners-section.tsx::OwnersSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7528ba4d998b980f6dae2843e3e1aaf2279698a0593a66c9dbf57813d16ea444
status: llm_drafted
---

# OwnersSection

## Purpose

Displays the list of current boat owners and provides controls for managing membership. It allows the current user (if they are an owner) to propose the removal of a co-owner or invite a new one via the `InviteCoownerDialog`. This component is a sub-section of the boat management interface, distinct from the general boat profile as it specifically handles the identity-based permissions of the vessel.

## Invariants

- **`isOwner` check** — The "Propose removal" button and "Invite co-owner" button are only rendered if `isOwner` is true.
- **`currentUserUuid` exclusion** — The removal logic prevents a user from removing themselves by checking `o.person_uuid !== currentUserUuid`.
- **`onMutated` callback** — Any successful call to `boatApi.coownerRemove` or the `InviteCoownerDialog` success handler must trigger `onMutated` to refresh the parent's state/data.
- **`boatUuid` dependency** — All mutations (removal and invitation) are scoped to the provided `boatUuid`.

## Gotchas

- **Removal is a "proposal" not a direct deletion** — Per the `confirm` dialog in the `remove` function, the action is framed as a proposal. This aligns with the logic in commit `47688ac` where membership requirements were tightened.
- **Mobile layout constraints** — Per commit `3402684`, the component uses `max-md:w-full` on the invite button to ensure stack actions do not overflow the viewport on smaller screens.
- **Invite UX fallback** — The component relies on `InviteCoownerDialog` to handle the complex logic of directory-first vs. upgrade-prompt flows (see commit `eb382d2`).

## Cross-cutting concerns

- **Auth**: Requires `isOwner` to be true to access mutation buttons.
- **Side effects**: Triggers `onMutated` which typically refreshes the boat profile or owner list in the parent view.

## External consumers

None known.
