---
node_id: concorda-web::src/components/dashboard/regatta-help-dialog.tsx::DocBadge
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7b6fc6a9db821e75c235a322716d58dc2c9b258799fa0760f7fe2fa8e01f8a0e
status: current
---

# DocBadge

## Purpose

The `DocBadge` is a specialized, low-level UI component used to wrap text or icons within a small, high-contrast container. It is a specialized version of the standard `Badge` component, specifically styled with a fixed height (`h-5`) and small font size (`text-[10px]`) to serve as an annotation within the `RegattaHelpDialog` documentation examples.

## Invariants

- **Fixed dimensions.** The component uses a hardcoded height of `h-5` and `text-[10px]` to ensure it fits within the tight vertical constraints of the "Example" section in the help dialog.
- **Visual style.** It uses the `variant="outline"` property of the base `Badge` component to maintain a subtle, non-intrusive appearance.
- **Content type.** It accepts `ReactNode` as children, allowing for both text strings and icon components (like `CalendarCheck`).

## Gotchas

- **Manual styling overrides.** Because it relies on specific utility classes (`text-[10px] px-1.5 py-0`) to fit the documentation layout, changing the base `Badge` component's default padding or font size could cause layout shifts in the `RegattaHelpDialog` example section.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None. This is a purely presentational component used for documentation/instructional purposes within the `RegattaHelpDialog`.

## External consumers

None known.
