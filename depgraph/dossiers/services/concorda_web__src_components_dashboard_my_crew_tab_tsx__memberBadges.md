---
node_id: concorda-web::src/components/dashboard/my-crew-tab.tsx::memberBadges
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3a7a2b517be938237b548019b0adef53afad4ba4e0a30089f174eee64dc8f4f3
status: llm_drafted
---

# memberBadges

## Purpose

The `memberBadges` helper generates the visual status indicators for a crew member within the `MyCrewTab`. It renders two distinct pieces of information: the member's `position` (as an outline badge) and their current `status` or `role` (as a colored badge). This distinguishes between a person's functional role (e.g., "Owner") and their relationship status to the boat (e.g., "active" or "invited").

## Invariants

- **Input is a `BoatCrewMember` object.** The function expects a valid member object containing at least a `status` and a `position` string.
- **`position` is optional.** If `member.position` is falsy, the first badge is omitted from the fragment.
- **`status` determines the color variant.** The `STATUS_COLORS` mapping dictates the `variant` prop passed to the `Badge` component.
- **Text content is conditional.** If the status is `"active"`, the badge displays the `member.role`; otherwise, it displays the `member.status` string.

## Gotchas

- **Status/Role ambiguity.** Per the logic in `memberBadges`, if a user is `"active"`, the badge shows their `role` (e.g., "Skipper"), but for any other status (e.g., "invited"), it shows the status itself. This ensures "active" members are identified by their functional role while others are identified by their invitation state.
- **Color mapping fallback.** If `member.status` does not match a key in `STATUS_COLORS`, the badge defaults to `"secondary"`.

## Cross-cutting concerns

- **Auth**: None. This is a pure UI helper.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: None.

## External consumers

- Internal to `MyCrewTab` via the `SortableCrewCard` component.
