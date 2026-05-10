---
node_id: concorda-web::src/lib/utils.ts::cn
node_kind: service
feature: ui
last_reviewed: 2026-05-09
last_reviewed_against_hash: b4e6c04dd4254924854e1b28739d63fc5d2a8b84af89e24a907a052c18f1249a
status: current
---

# cn

## Purpose

The shadcn-standard className helper. Combines `clsx` (conditional class names) and `tailwind-merge` (resolves conflicting Tailwind utilities to the last specified). 40 components depend on it. Every JSX `className={cn(...)}` you see is this.

## Invariants

- **Order matters for tailwind conflicts.** `cn("p-2", "p-4")` returns `"p-4"` because `twMerge` resolves the conflict by keeping the *last* utility. Component authors leverage this to allow consumers to override defaults: `cn("p-2 bg-blue-500", className)` lets the caller pass `className="p-8"` to get `p-8` in the final output.
- **Falsy values are dropped.** `cn("base", isActive && "active", undefined, null)` is safe.
- **Returns a single space-joined string.** Pass it directly into `className=`.

## Gotchas

- **Don't `cn(cn(...))`** — works (idempotent enough) but produces the same result with extra cycles. Flatten arguments.
- **Tailwind classes you've added via arbitrary values (`p-[12px]`) are not deduplicated** the same way as named utilities. `cn("p-[12px]", "p-2")` returns both because tailwind-merge has a rule table for named utilities only.
- **40 dependents.** Renaming or signature change is a sweep. The function is so trivial it shouldn't change, but if you ever need to (e.g., to add a debug logger), the structural_hash flip will mark every consumer for review.

## Cross-cutting concerns

- **Tailwind config:** the merge rules in `tailwind-merge` are tied to the Tailwind config indirectly. Adding a new variant or custom utility prefix can require a `twMerge` extension to dedupe correctly.
- **shadcn convention:** every shadcn component (Button, Card, etc.) uses this. Reading their source is the easiest way to learn the canonical pattern.

## External consumers

- N/A — purely internal to the web app.

## Open questions

- None — this is a stable utility.
