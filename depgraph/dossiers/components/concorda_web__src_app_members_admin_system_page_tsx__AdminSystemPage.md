---
node_id: concorda-web::src/app/members/admin/system/page.tsx::AdminSystemPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f6592db7c2f778298b7b77458fee031256ba070aa2861e8a3902be8bb848bf15
status: llm_drafted
---

# AdminSystemPage

## Purpose

The central administrative dashboard for managing organization-wide settings. It provides a single interface to configure the `org_name`, `app_title`, timezone, and default membership, while also managing rate-limiting thresholds and error notification settings. It is the primary control plane for the organization's identity and operational constraints.

## Invariants

- **Uses `adminOrgConfigApi` for all mutations** to ensure the `OrgConfigData` shape is respected.
- **`DEFAULT_MEMBERSHIP_NONE` is the constant `__none__`** used to represent a null state in the select dropdown.
- **Rate limit inputs are managed as strings** in local state to allow for empty/cleared inputs before being cast to numbers for the API.
- **`constantsManager.refresh()` must be called after a successful config update** to propagate changes to the rest of the application.

## Gotchas

- **Rate limit inputs require string state.** Per commit `c1766b4`, the `register_rate_limit_max` and `register_rate_limit_window_seconds` must be stored as strings in the component state to prevent issues when a user clears the input field.
- **`adminStorageApi.get()` failure is swallowed.** The `useEffect` catch block for the storage API call is empty, meaning a failure to fetch storage info will not prevent the rest of the page from loading, but the `storage` state will remain `null`.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges (implicitly handled by the `adminOrgConfigApi` and `adminStorageApi` endpoints).
- **Side effects**: A successful save triggers `constantsManager.refresh()`, which updates the global configuration used by the rest of the application (e.g., branding, timezones, and rate-limiting logic).

## External consumers

None known.
