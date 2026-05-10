---
node_id: concorda-web::src/app/members/admin/products/[category]/page.tsx::CategoryProductsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 33d188b1b65df78eae7cdcb103ea3867eb06de47679122ca5620f5eded4ae514
status: current
---

# CategoryProductsPage

## Purpose

The administrative view for managing products within a specific category (e.g., "Membership" or "Sailing"). It provides a dashboard to list, create, edit, and delete products, including specialized fields for age requirements and feature grants. It is distinct from the public-facing product views by providing full CRUD capabilities via the `adminTemporalProductsApi`.

## Invariants

- **Category-driven routing**: The page relies on the `category` param to filter the `adminTemporalProductsApi.list` call.
- **Merchandise dependency**: If the category is "Membership", the component fetches and displays available merchandise via `adminMerchandiseApi.list` to allow linking products to specific merchandise items.
- **Sorting**: Products are sorted by `sort_order` immediately after fetching to ensure the UI reflects the intended display sequence.
- **Form state structure**: The `formData` object includes specific boolean flags for feature grants (`grants_event_discount`, `grants_crewfinder`, etc.) which are part of the product's identity.

## Gotchas

- **Mobile layout regression**: Per commit `f19f3d7`, admin sub-directory tables require a paired desktop+card layout to prevent breakage on small screens.
- **Dialog width constraints**: Per commit `0564f06`, admin dialogs must cap their width and stack the footer on `<md` breakpoints to avoid UI overflow during product editing.
- **Form reflow**: Per commit `019f6e3`, the single-column form reflow is required for mobile-friendly admin grid editing.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges (implied by the `admin` path and use of `adminTemporalProductsApi`).
- **Side effects**: Updates to products in this view affect the visibility and availability of features in the `boatfinder` page and the `crew management` modules.

## External consumers

None known.
