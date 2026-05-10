---
node_id: concorda-web::src/app/members/admin/delegates/page.tsx::AdminDelegatesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0232860a6df90f0ab1a5388e0ecf70310dd6271b1f90ac11e06c5fed53e3dc8c
status: llm_drafted
---

# AdminDelegatesPage

## Purpose

The administrative view for managing and viewing club delegates. It fetches a list of yacht clubs and their associated contact information via `adminApi.delegates()` and renders them in a responsive grid of cards. This page is intended for organization administrators to identify key points of contact for each club.

## Invariants

- **Requires `admin.delegates.view` permission** via the `PermissionGate` component.
- **Fetches data on mount** using `adminApi.delegates()`.
- **Returns an empty array on error** — if the API call fails, the UI displays the "No clubs found" state rather than crashing.
- **Uses `DelegateInfo[]` type** for the state to ensure type safety for the club and delegate properties.

## Gotchas

- **Type strictness required** — per commit `e38ad05`, this page previously suffered from type errors when using `Record<string, unknown>`; it must use the explicit `DelegateInfo[]` type from the API library to avoid build failures.
- **Empty state fallback** — if the API returns an empty list, the UI renders a specific "No clubs found" card with a `Building2` icon to prevent a blank screen.

## Cross-cutting concerns

- **Auth**: Protected by `PermissionGate` with `admin.delegates.view`.
- **Side effects**: None.

## External consumers

None known.
