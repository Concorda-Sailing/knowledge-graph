---
node_id: concorda-web::src/lib/api.ts::paymentsApi.getConfig
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0d06779a1f86d8c3f107b72ebd888732dee36e96d99bf439c4ae5b2bf5c17f33
status: llm_drafted
---

# paymentsApi.getConfig

## Purpose
Client-side mirror for fetching the public Stripe configuration (publishable key + enabled flag) needed to initialize Stripe Elements / `loadStripe`. Three call sites consume it: the public event detail page (`/events/[slug]`) for ticket purchase, the join/register flow for paid memberships, and the in-app `MembershipUpgrade` component for upgrades from a logged-in profile. It exists so the frontend never hardcodes a publishable key and can flip between test/live/disabled modes via the DB-backed `PaymentConfig` row without a redeploy. A future Claude editing this should treat it as the single source-of-truth for "is Stripe ready" on the web client.

## Invariants
- Endpoint is **public** — no auth header, no `current_user` dependency on the backend (`routers/payments.py:49`). Must stay callable from the unauthenticated event page and the pre-account register flow.
- Response shape is exactly `{ publishable_key: string; enabled: boolean }`. `publishable_key` is `""` (empty string, not null) when disabled — consumers gate on `enabled && publishable_key`.
- Returns **no secrets** — only the publishable key, never the secret key or webhook signing secret. Backend comment enforces this contract.
- `enabled` is derived: requires both a non-empty secret_key AND `mode != "disabled"`. A test-mode config with no secret reads as disabled.
- Uses `fetchApi` (unauthenticated), not `fetchApiAuthenticated`. Do not "upgrade" it to authenticated — it would break the events page and register flow.

## Gotchas
- The register page (`join/register/page.tsx:128,134`) falls back to `process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` when the API call fails or returns disabled. The other two consumers do **not** — they silently leave Stripe uninitialized. If you "fix" register to match, double-check whether that env var is still populated in prod (DB config has been the source of truth for a while).
- DB-backed `PaymentConfig` overrides env vars when `mode` is `"test"` or `"live"`. Mode `"env"` is the fallback path that reads `STRIPE_PUBLISHABLE_KEY` from environment. Mode `"disabled"` always returns `enabled: false`.
- The events page calls this during SSR-able render (page is public); it works because the endpoint is unauthenticated. If the auth middleware is ever tightened to require a session for unrelated reasons, this call site breaks first.
- No "mode" field is exposed to the client even though backend tracks one — UI cannot distinguish test-mode from live-mode. If we ever need to show a "Test mode" banner on the checkout, the response shape needs to grow.

## Cross-cutting concerns
- **Auth**: none. Public route, no rate limit on this endpoint specifically (rate limit lives on `/create-intent`).
- **Side effects**: none — pure read of `PaymentConfig` singleton.
- **Caching**: not currently cached client-side; each consumer fetches on mount. Cheap enough but means a flicker before Stripe Elements mount.
- **Failure mode**: a 5xx here disables checkout UI silently in two of three consumers. Worth surfacing if we add observability.

## External consumers
None known. The Expo iOS app does not currently invoke `/api/payments/config` (Stripe payments on mobile haven't shipped). Webhooks and scheduled jobs do not depend on this endpoint.

## Open questions
- Should we expose `mode` ("test" vs "live") so the UI can warn users on test-mode checkouts? Currently they look identical.
- Should the response be cached (e.g. SWR with long stale time) to avoid the per-mount fetch on the events page where it runs for every visitor?
