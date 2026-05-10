---
node_id: concorda-web::src/app/members/admin/accounting/page.tsx::AdminAccountingPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: afa799d8b84e11cf6106218a1e22584d98ec0a773a62c0dd5e8942d9823f4fc1
status: current
---

# AdminAccountingPage

## Purpose

The administrative dashboard for viewing high-level financial metrics and transaction history. It provides a summary of revenue streams (Memberships, Events, and Book Pages) and provides a placeholder for transaction exports. This page is intended for organization admins to monitor the financial health of the club.

## Invariants

- **Permission-gated** — The entire view is wrapped in a `PermissionGate` requiring `admin.accounting.view`.
- **Data-driven summary** — The current implementation uses hardcoded placeholder data (e.g., `$0.00` and empty `transactions` array) and must be wired to the API to reflect real-time revenue.
- **Export functionality** — The "Export Transactions" button is a structural placeholder that must eventually trigger a download of the transaction history.

## Gotchas

- **Placeholder state** — As of commit `54d6153`, the page contains static UI components and placeholder data; it does not yet fetch live data from the backend.

## Cross-cutting concerns

- **Auth**: Requires `admin.accounting.view` permission via `PermissionGate`.
- **Side effects**: N/A.

## External consumers

None known.
