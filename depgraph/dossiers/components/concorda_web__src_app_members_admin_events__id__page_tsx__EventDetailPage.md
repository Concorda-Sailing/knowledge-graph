---
node_id: concorda-web::src/app/members/admin/events/[id]/page.tsx::EventDetailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c03900cbb0b4bb6aa46d614fbb3ec16749edab501479a27e449d7d14d08b2b11
status: current
---

# EventDetailPage

## Purpose

The primary administrative interface for creating and managing event details. It handles three distinct modes—`view`, `edit`, and `new`—determined by the presence of an ID in the URL. It manages complex state for event metadata (name, location, category), image uploads, and nested entities like tickets and registrations.

## Invariants

- **Permission-gated access**: The entire view is wrapped in a `PermissionGate` requiring at least one of `events.create`, `events.edit`, or `events.view`.
- **Mode-based routing**: If the `id` param is `"new"`, the component enters creation mode; otherwise, it fetches and populates existing event data.
- **Category-driven navigation**: The `backUrl` logic is tied to the `formData.category`; "regatta" events link back to `/races`, while "social" events link to `/socials`.
- **Stateful form-to-API mapping**: Form fields (like `date` and `end_date`) must be converted via `orgInputToUtcIso` before being sent to the API to ensure timezone consistency.

## Gotchas

- **Mobile layout reflow**: Per commit `f19f3d7` and `019f6e3`, admin sub-directory tables and forms require specific single-column stacking and width caps to prevent layout breakage on small screens.
- **Form field dependency**: The `category` field is not just a string; it dictates the `backUrl` destination. Changing the category mid-edit can change the intended navigation path.
- **Image upload state**: The component manages three distinct states for images (`imageUrl`, `pendingImageFile`, and `pendingImagePreview`) to handle the transition from local file selection to server-side persistence.

## Cross-cutting concerns

- **Auth**: Requires `events.create`, `events.edit`, or `events.view` via `PermissionGate`.
- **Side effects**: Updates to this page (via the API) will affect the visibility and data displayed in the event list/calendar views.

## External consumers

None known.
