---
node_id: concorda-web::src/app/members/admin/products/merchandise/page.tsx::MerchandisePage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5e4e1e1d9768e79cdc960274969d92244c771db04c25bc7941abc0445c984fe7
status: current
---

# MerchandisePage

## Purpose

The administrative dashboard for managing organization-specific merchandise. It provides a CRUD interface for creating, editing, and viewing merchandise items, including stock numbers, pricing, and availability status. It is the primary interface for admins to manage physical or digital goods sold by the organization.

## Invariants

- **Uses `adminMerchandiseApi`** for all data operations (list, create, update).
- **`showInactive` toggle controls visibility** via the `include_inactive` parameter in the `list` call.
- **`sort_order` defaults to `items.length`** during creation to append new items to the end of the list.
- **Form state is local to the component**; opening a dialog resets the `formData` to prevent stale data from leaking between edit sessions.

## Gotchas

- **Mobile layout reflows** — per commit `f19f3d7`, admin sub-directory tables must use a paired desktop+card layout to remain usable on mobile.
- **Dialog width constraints** — per commit `0564f06`, dialogs in this admin section must cap their width and stack the footer on `<md` breakpoints to prevent UI breakage on small screens.
- **Single-column form reflow** — per commit `019f6e3`, any new fields added to the merchandise forms must follow the single-column reflow pattern used in admin grids to maintain mobile compatibility.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges (implied by the `admin` path and `adminMerchandiseApi` usage).
- **Side effects**: Changes to merchandise (price, stock, or name) directly impact the public-facing store/product pages.

## External consumers

None known.
