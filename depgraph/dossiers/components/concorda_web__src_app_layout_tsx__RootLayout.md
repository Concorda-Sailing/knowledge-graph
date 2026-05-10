---
node_id: concorda-web::src/app/layout.tsx::RootLayout
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b0c0d256589f4f359b6abc9af1c28140c34f8011b370a2d2ba8cf7b2ff8edd59
status: current
---

# RootLayout

## Purpose

The top-level layout component for the MBSA Clubhouse web application. It establishes the global document structure, including the HTML/Body wrapper, typography via the `libreFranklin` variable, and the essential provider hierarchy required for the application to function. It serves as the entry point for all authenticated and real-time features.

## Invariants

- **Hydration stability:** Uses `suppressHydrationWarning` on the `<html>` tag to prevent mismatches caused by `ThemeProvider` or browser-specific attributes.
- **Provider Order:** The hierarchy is strictly `ThemeProvider` -> `Suspense` -> `AuthProvider` -> `WebSocketProvider`.
- **Font injection:** The `libreFranklin.variable` must be present on the `<body>` to ensure the `--font-libre-franklin` CSS variable is available to all child components.

## Gotchas

- **Suspense requirement:** Per commit `ceb01d2`, the `AuthProvider` must be wrapped in a `<Suspense>` boundary. Failure to do this causes prerender errors when the provider attempts to use `useSearchParams` or other hook-based navigation logic during the build phase.
- **Theme/Auth dependency:** Because `WebSocketProvider` is a child of `AuthProvider`, any websocket connection logic that relies on user identity or permissions must be aware that the auth context is established upstream.

## Cross-cutting concerns

- **Auth**: Provides the `AuthProvider` context used by all authenticated routes.
- **Websocket**: Initializes the `WebSocketProvider` which manages real-time event streams for the entire app.
- **Side effects**: The layout structure dictates the rendering context for the entire dashboard, admin panels, and agent interfaces.

## External consumers

None known.
