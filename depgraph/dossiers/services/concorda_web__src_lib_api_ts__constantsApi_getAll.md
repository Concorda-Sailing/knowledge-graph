---
node_id: concorda-web::src/lib/api.ts::constantsApi.getAll
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c5258471074a5fdc99d17cbe3fa91953c2d73474b162ae092606c38f077244fb
status: llm_drafted
---

# constantsApi.getAll

## Purpose

Client-side mirror for the server's vocabulary / enum constants — the single GET that pulls back the union of `positions`, `experience_levels`, `certifications`, `shirt_sizes`, `member_categories`, `regions`, plus org-branding fields (`org_name`, `logo_url`, `timezone`, `default_membership_slug`, `app_title`). Components consume it via `useConstants()` (which sits on top of the singleton `constantsManager`) so dropdowns, badges, and tz-aware formatters draw from one source instead of hardcoding string literals. Preferred over inlining values because the backend `routers/constants.py` is the canonical list (e.g. positions get coordinate metadata via `POSITION_LOCATIONS`, experience levels carry `value/label` pairs) and `org_config.timezone` is read from DB so a self-hosted org gets its own TZ without code changes.

## Invariants

- Endpoint is `GET /api/constants`, **unauthenticated** — it's called via `fetchApi`, not `fetchApiAuthenticated`. Login screens and pre-auth pages can read it.
- Response shape must stay aligned with `ConstantsResponse` (api) and `AppConstants` (types.ts:2397). Adding a field requires updating both, plus `DEFAULT_CONSTANTS` in `constants-manager.ts` (fallback when the fetch fails).
- `timezone` is the org default (DB `OrgConfig.timezone` → fallback `"America/New_York"`); `useConstants()` re-defaults to `"America/New_York"` if the field comes back empty. This is what `lib/datetime.ts::formatInOrgTz` reads — see its dossier.
- Singleton cache: `constantsManager` fetches once per page load, dedupes concurrent calls via `fetchPromise`, and notifies subscribers. There is no TTL — values are stable for the session.
- On failure the manager swallows the error, logs to console, and serves `DEFAULT_CONSTANTS`. Callers see a value, never `null`.

## Gotchas

- `DEFAULT_CONSTANTS.positions` in `constants-manager.ts` is **not** the same list as `POSITIONS` in `routers/constants.py` (defaults include "Navigation" and "All"; canonical list has Navigator, Tactician, Helm, Main/Jib Trim, Bow, Pit, Mast, Grinder, Ballast). If the API is unreachable on first paint, downstream pickers see the wrong vocabulary — refreshing once the API is up fixes it but stale renders can mislead.
- `routers/constants.py` declares `SHIRT_SIZES` and `MEMBER_CATEGORIES` twice (lines 83/85 and 97/99). Harmless, but edit the second pair if you're changing values — Python takes the last assignment.
- The response shape is the lists above plus org branding. If a future feature needs course-type or scoring-system enums, they have to be added here (and to the Pydantic model) — they're not silently present.
- `getAll` is unauthed but `getPositions` / `getExperienceLevels` (sibling methods) are also unauthed and return subsets — `getAll` is almost always the right call; the per-endpoint methods exist but are barely used.
- Caching is process-local. After an admin edits `OrgConfig` (logo, timezone, app title), open tabs keep the old values until reload or until something calls `constantsManager.refresh()`.

## Cross-cutting concerns

- **Auth**: none. Safe to call from logged-out pages (login, signup, public landing).
- **Timezone propagation**: this endpoint is the upstream of every `formatInOrgTz` call; ~30+ components read `timezone` via `useConstants()`. Changing the field name or default is a sweeping break.
- **Branding**: `org_name`, `logo_url`, `app_title` feed `org-brand.tsx`, `yearbook-header.tsx`, `event-qr-code.tsx`. Document title and email-template branding pull from here too.
- **Default membership**: `default_membership_slug` resolves `org_config.default_membership_id` to a `TemporalProduct.slug` — used by signup flows to pick a default plan without hardcoding UUIDs.
- **Side effects**: none server-side — pure read.

## External consumers

None known. Web app only; the Expo iOS app has its own constants path. No webhooks, scheduled jobs, or third-party integrations call `/api/constants`.

## Open questions

- Should `constantsManager` invalidate after a known org-config mutation (admin save) instead of waiting for reload? Today, admins editing branding don't see the change in their own session until refresh.
- The default-fallback `positions` list diverging from canonical is a latent bug — worth either deleting the fallback and showing a loading state, or syncing it to the real list.
