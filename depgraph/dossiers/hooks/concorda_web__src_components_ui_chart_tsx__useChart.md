---
node_id: concorda-web::src/components/ui/chart.tsx::useChart
node_kind: hook
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6433da73d6b0f5a8033fc293709f358d97b831edc0f928a8d1f37590748ecf9b
status: current
---

# useChart

## Purpose

Provides access to the `ChartConfig` context within a Recharts-based component tree. It is a consumer hook designed to be used by children of `<ChartContainer />` to retrieve theme-specific color variables and configuration. Use this instead of passing props down manually when a sub-component needs to access the `config` object (e.g., for custom tooltips or legend items).

## Invariants

- **Requires `<ChartContainer />` context.** Calling `useChart()` outside of a `ChartContainer` provider will throw a runtime error.
- **Returns `ChartContextProps`.** The returned object contains the `config` object used to drive CSS variables.
- **Context is read-only.** The hook returns the context value provided by the nearest `ChartContainer` up the tree.

## Gotchas

- **Throws error if used incorrectly.** Per the source, `useChart` explicitly throws `new Error("useChart must be used within a <ChartContainer />")` if the context is undefined. This is a hard failure, not a silent null return.
- **CSS Variable dependency.** The `ChartContainer` uses `ChartStyle` to inject colors into the DOM via `dangerouslySetInnerHTML`. If a component using `useChart` expects a color to be available via a CSS variable (e.g., `--color-key`), ensure that the key is actually defined in the `config` passed to the container.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
