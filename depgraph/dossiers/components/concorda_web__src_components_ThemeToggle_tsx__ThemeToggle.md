---
node_id: concorda-web::src/components/ThemeToggle.tsx::ThemeToggle
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e7307dbb0e3211bb8791d94bff927d50bfdc071dbb8600d7cd1fe95a3f220fbe
status: current
---

# ThemeToggle

## Purpose

A UI component that allows users to toggle between light and dark color modes. It wraps the `useTheme` hook from `next-themes` to provide a seamless transition between themes. Use this component when a global theme switch is required in a header or navigation bar.

## Invariants

- **Uses `next-themes` context.** The component relies on a `ThemeProvider` being present higher up in the component tree to function.
- **Toggles between exactly two states.** The logic is hardcoded to switch between `"light"` and `"dark"`.
- **Accessibility is handled via `sr-only`.** The button includes a screen-reader-only span to ensure the purpose of the icon-only button is clear to assistive technologies.

## Gotchas

- **Visual transition dependency.** The `Sun` and `Moon` icons use CSS classes (`rotate-0`, `scale-100`, `dark:-rotate-90`, etc.) to handle the animation. If the transition logic is modified without updating the `dark:` variants, the icon swap will appear jarring or broken.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Changes the visual appearance of the entire application via the `next-themes` provider.

## External consumers

None known.
