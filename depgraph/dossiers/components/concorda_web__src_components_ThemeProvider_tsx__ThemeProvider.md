---
node_id: concorda-web::src/components/ThemeProvider.tsx::ThemeProvider
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 312abe5b574514539aa6b1bf080a214afb1138b5dc4dffe519cbbe8c4dbe236b
status: llm_drafted
---

# ThemeProvider

## Purpose

Provides a centralized context for managing light/dark mode and system-level theme-switching via `next-themes`. It wraps the application in a `NextThemesProvider` to ensure that any component consuming a theme context (e.g., via `useTheme`) receives consistent state. This is the top-level provider for the web application's visual state.

## Invariants

- **Uses `next-themes` under the hood** — the component is a thin wrapper around `NextThemesProvider`.
- **Requires `"use client"`** — as a React Context provider, it must be a Client Component to manage state and side effects.
- **Prop-forwarding** — all `ThemeProviderProps` (like `attribute`, `defaultTheme`, or `enableSystem`) are passed directly to the underlying provider.

## Got-chas

- **Recent structural changes** — per commit `fd7fd0f`, the application is undergoing a URL restructure and adding staging Docker support; ensure theme-specific CSS variables or local storage keys do not conflict with new staging environments.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: affects all components relying on CSS variables or `useTheme` hooks, including the dashboard and profile views.

## External consumers

None known.
