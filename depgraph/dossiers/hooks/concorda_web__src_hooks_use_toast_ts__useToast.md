---
node_id: concorda-web::src/hooks/use-toast.ts::useToast
node_kind: hook
feature: ui
last_reviewed: 2026-05-09
last_reviewed_against_hash: 2272a6d165e7f605d55cba62af192d090f659dd07b07df311a1f870c9668ddc2
status: current
---

# useToast

## Purpose

The single source of toast notifications for the entire web app. Returns `{ toasts, toast, dismiss }`. Components call `toast({title, description, ...})` to show a notification; the global `<Toaster />` (mounted once in the root layout) renders the active toast list.

This is a **shadcn-style** toast hook — the implementation is module-level state shared across all consumers, not a context. There is one toast queue per page load; `useToast` returns a snapshot synchronized via a listener pattern.

## Invariants

- **`TOAST_LIMIT = 1`.** Only one toast is shown at a time. New toasts replace the current one rather than queueing. Don't change this without designing a stacking UX — most callers assume the most recent message is the only one visible.
- **`TOAST_REMOVE_DELAY` is intentionally large** (1,000,000 ms ≈ 16 minutes). Toasts dismiss themselves on `open=false` user gesture; the long delay just controls how long a dismissed toast lingers before being garbage-collected from state. Treat as an internal cleanup constant.
- **`memoryState` is module-scoped.** It survives across rerenders and across components but resets on full page reload. Calling `toast(...)` from anywhere works without prop-threading.
- **`<Toaster />` must be mounted exactly once** in the root layout for toasts to render. Mounting it twice doubles every toast; not mounting it means `toast(...)` calls are no-ops visually.
- **The standalone `toast(...)` function does NOT need a hook caller.** It can be invoked from outside React components (e.g., from a global error handler). The hook is required only when a component needs to read `toasts` for rendering.

## Gotchas

- **State is not in a context.** That's intentional (avoids re-renders cascading through every consumer) but it means: server-rendered components do not see this state. Toasts only work on the client side. Calling `toast(...)` during SSR is a silent no-op.
- **45 web nodes consume `useToast`.** Most just call `toast({title, description, variant})` after a mutation. The shape `{title, description, variant}` is the de-facto API; renaming any of these keys breaks every consumer.
- **`onOpenChange` triggers `dismiss`.** Don't set a custom `onOpenChange` without remembering to call `dismiss()` yourself, or the toast state will leak.
- **The listener array is leaked on hot reload.** In dev, a hot reload that re-mounts `useToast` adds a new listener but the old one stays referenced by `memoryState`. Hard refresh if toast state seems "doubled" in dev.

## Cross-cutting concerns

- **Used after every mutation.** Pattern: `await api.x(); toast({title: "Saved"})` or `toast({variant: "destructive", title: "Error", description: err.message})`.
- **Variant convention:** `default` and `destructive`. Some callers also pass `success` — this is rendered the same as `default` and should be unified.

## External consumers

- N/A — purely internal to the web app.

## Open questions

- Should toasts queue (`TOAST_LIMIT > 1`) instead of replacing? Today rapid mutations cause earlier toasts to be invisible.
- Standardize the `success` vs `default` variant overlap.
