---
node_id: concorda-web::src/components/dashboard/membership-card.tsx::MembershipCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 63ccbc918b7a0b1c31ca7cd99da46b08220de11c908df3de53cbf33312c54c4e
status: current
---

# MembershipCard

## Purpose

Displays a high-level summary of a user's membership status within the dashboard. It provides a visual indicator of membership type (e.g., "Boat Owner") and the current status (Active, Expired, or Pending) alongside an expiration date. Use this component for quick-glance status updates rather than detailed billing or subscription management.

## Invariants

- **`status` is a union type**: Must be exactly `"active" | "expired" | "pending"`.
- **`expirationDate` is a string**: Expects a pre-formatted human-readable date string (e.g., "December 31, 2026") rather than a Date object or ISO string.
- **Default values are provided**: If props are missing, it defaults to "Member", "Boat Owner", "active", and a hardcoded 2026 date.

## Gotchas

- **Hardcoded defaults**: The component uses a hardcoded expiration date (`"December 31, 2026"`) as a fallback. If the parent component fails to pass a valid `expirationDate`, the UI will display this static value rather than an empty state or error.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
