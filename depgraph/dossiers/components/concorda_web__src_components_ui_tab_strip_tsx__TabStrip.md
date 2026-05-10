---
node_id: concorda-web::src/components/ui/tab-strip.tsx::TabStrip
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 003cb77280592509f9bd55f32918dda895edf956516fd568bf4f08789a415d5b
status: llm_drafted
---

# TabStrip

## Purpose

A horizontal navigation component that provides scrollable tab navigation with directional chevron buttons. It is used when the number of available tabs exceeds the container width, ensuring the UI remains usable on smaller viewports or narrow layouts. Unlike a standard static tab list, this component manages its own scroll state and visibility of navigation controls via a `ResizeObserver`.

## Invariants

- **`activeId` must be a string** matching one of the `tabs[].id` values to ensure the active state is visually synchronized.
- **`onActiveChange` is the primary interaction handler** for switching the active tab.
- **`tabs` is an array of `TabStripTab` objects**, where each tab can optionally include a `count` for numeric indicators.
- **Scroll buttons are absolute-positioned** relative to the container, using a gradient overlay to blend with the background.

## Gotchas

- **Avoid dependency on `tabs.length` for scroll visibility.** Per commit `4f2cb58`, the component no longer relies on the number of tabs to determine if scrollers are needed; it relies strictly on the `scrollLeft` position of the internal `scrollRef` to show/hide the `showLeft` and `showRight` buttons.
- **`scrollBy` uses smooth behavior.** The `scrollBy` function is hardcoded with `{ behavior: "smooth" }`, which may feel sluggish if used for rapid-fire navigation.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
