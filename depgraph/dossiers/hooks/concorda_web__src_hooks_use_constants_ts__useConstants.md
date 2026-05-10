---
node_id: concorda-web::src/hooks/use-constants.ts::useConstants
node_kind: hook
feature: app-config
last_reviewed: 2026-05-09
last_reviewed_against_hash: 599d09bc2daee4aa38e9f51c47772ddc9293af26964225e4bad5ab01bb63e1c2
status: current
---

# useConstants

## Purpose

Read-only access to server-provided app constants: position list, experience levels, certifications, shirt sizes, member categories, org name, logo URL, **timezone** (the org timezone — passed to `formatInOrgTz` everywhere), default membership slug, app title.

Backed by a singleton `constantsManager` that fetches `/api/constants` on first use and subscribes to updates. Cached across component remounts. 44 web components depend on it — making it tied with `useToast` for the most-used hook in the app.

## Invariants

- **`/api/constants` is unauthenticated.** Constants need to be available on `/login` and other public pages, so don't add auth-required fields here. Anything user-specific belongs on `/api/profile` or similar.
- **`timezone` falls back to `"America/New_York"`.** Concorda is currently MBSA-only and that's the right default. When/if multi-org lands, the fallback strategy needs revisiting; for now the org admin sets the right value via `/api/admin/org-config` and the constants endpoint surfaces it.
- **`appTitle` falls back to `"MBSA Clubhouse"`.** Same multi-org caveat. Browser title bars and the sidebar use this.
- **The hook reads the cache synchronously on mount** — `useState(constantsManager.getConstants())`. The first render of any consumer can see partial data; check `isLoaded` if you need certainty.
- **Subscription cleans up on unmount.** The unsubscribe pattern is critical: forgetting it leaks the listener and rerenders dead components.

## Gotchas

- **The constants object is shared across all consumers.** Mutating it directly mutates everyone's view. Always treat as immutable.
- **`useEffect` runs only on mount** (`deps: []`). It triggers a fetch if not loaded; subsequent reloads must call `refresh()` explicitly.
- **`refresh()` clears `isLoading`** itself, but the subscription pattern can race: if a subscriber updates `isLoading=true` between when refresh starts and when refresh's own setIsLoading runs, you might briefly see the wrong state. Acceptable today but worth knowing.
- **`AppConstants` is the source of truth for the constant *shape*.** It comes from `@/lib/api`. Adding a new field requires changes in 3 places: api.ts (type), this hook (return mapping), and the API's `/api/constants` handler.

## Cross-cutting concerns

- **Timezone:** every `formatInOrgTz(iso, useConstants().timezone, opts)` call site — see `formatInOrgTz` dossier.
- **Branding:** `orgName`, `logoUrl`, `appTitle` are used in headers, emails, and the sidebar.
- **Forms:** `positions`, `experienceLevels`, `certifications`, `shirtSizes`, `memberCategories` populate dropdowns across the app.
- **Caching:** `constantsManager` keeps the values in memory; refreshing the page refetches, but a `<Suspense>` boundary won't help here (data is fetched in client code, not RSC).

## External consumers

- N/A — purely internal to the web app.

## Open questions

- Should constants be RSC-fetched and passed via root provider rather than client-fetched? Would shave the first-paint latency.
- Multi-org will require disambiguating which org's constants to load — needs a tenant-resolver before then.
