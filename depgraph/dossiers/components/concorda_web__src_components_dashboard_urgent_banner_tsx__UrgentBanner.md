---
node_id: concorda-web::src/components/dashboard/urgent-banner.tsx::UrgentBanner
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3bc717095f9171d471ad7123b9039a6170556b513b5a27ef0a0ff8e8b111b74d
status: llm_drafted
---

# UrgentBanner

## Purpose

Displays a high-visibility alert banner on the dashboard when time-sensitive approvals are pending. It acts as a visual nudge for administrators, surfacing the exact count of approvals expiring within the next 48 hours. It is distinct from the standard inbox view as it is a top-level dashboard notification rather than a list item.

## Invariants

- **Returns `null` if no urgent approvals exist.** The component must not render any DOM elements if `urgent.length === 0`.
- **Uses `usePendingApprovals` for state.** The component is a pure consumer of the `urgent` array provided by that hook.
- **Directs users to `/members/inbox`.** The "Review" button is hardcoded to this path to ensure the user lands exactly where the pending actions are located.

## Gotchas

- **Strict 48-hour threshold.** Per commit `fc86d01`, this is a "slim" implementation specifically for approvals with $\le$ 48h to expiry. Do not expand the logic to include all pending approvals, only those meeting this specific temporal threshold.

## Cross-cutting concerns

- **Auth**: Depends on `usePendingApprovals` which requires an active authenticated session to fetch the approval state.
- **Side effects**: The visibility of this banner is a direct indicator of the urgency of the user's inbox tasks.

## External consumers

None known.
