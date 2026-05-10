---
node_id: concorda-test::pages/admin/system.page.ts::AdminSystemPage.gotoSystem
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6280f4435899029296067e6143789943c3c487f2307c49570af78eff6c46aea0
status: llm_drafted
---

# AdminSystemPage.gotoSystem

## Purpose
Playwright POM navigation method that opens the admin system settings page at `/members/admin/system` and waits for `networkidle` before returning. It exists so individual specs don't repeat the URL + load-wait pair — three system-admin specs call it as their first action to land on the org-config screen (org name, timezone, logo) before exercising save / upload / validation flows. A future Claude editing this method should preserve the contract "after `await gotoSystem()`, the system settings form is fully hydrated and ready to interact with."

## Invariants
- Path stays `/members/admin/system` — the web app's admin router pins this route; sibling pages live at `/members/admin/email` and `/members/admin/payment` (see `gotoEmailConfig`, `gotoPaymentConfig`).
- Returns only after the page is interactable. Callers immediately query locators (`orgNameInput`, `timezoneSelect`) with no extra wait.
- No auth bootstrap here — specs are responsible for logging in as an org admin before calling this method. The page itself 403s for non-admins.

## Gotchas
- `waitForLoadState('networkidle')` is fragile: any background poll, websocket ping, or in-flight analytics call defers resolution and can flake under load. If the system settings page ever grows a periodic fetch (e.g., live config sync), swap to `waitFor` on a specific locator instead.
- The constructor defines locators with broad regex (`/organization name|org name/i`, `/timezone/i`, `/mode/i`). If the system page later embeds an unrelated "mode" or "timezone" control, locators will start matching the wrong element — flakes will surface in callers of `gotoSystem`, not here.
- Only one commit touches this file (initial scaffold `fd0c570`); no fix/revert history yet, so the failure modes above are theoretical, not observed.

## Cross-cutting concerns
- Touches the admin auth boundary — the `/members/admin/*` route tree requires `org_admin` role; navigating without that role produces a redirect or 403 that breaks downstream locator assertions with confusing "element not found" errors rather than an auth error.
- Side effects: none directly. But the page it loads exposes save handlers that mutate `Organization` config (name, timezone, logo URL); specs calling `gotoSystem` typically follow up by clicking `saveButton`, which writes to the API.
- Test isolation: per the project's test-env rules, this should only run against the test VM / Docker stack, never local — wiping/seeding behavior in the harness assumes that.

## External consumers
None outside the `concorda-test` repo. Three direct callers, all in `tests/admin/system-settings.spec.ts`.

## Open questions
- Should `gotoSystem` assert `org_admin` role (or a visible "System Settings" heading) before returning, so role failures surface as a clear auth error instead of cascading locator timeouts?
- `networkidle` vs. a sentinel-locator wait — worth standardizing across all `goto*` methods in the admin POMs before more pages are added.
