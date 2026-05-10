---
node_id: concorda-web::src/lib/api.ts::authedUrl
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 27dbe4695bcbdd514ffa02f60c12b7816ff553d91896a98f8575a98e46dff7d3
status: llm_drafted
---

# authedUrl

## Purpose

Builds a same-origin URL with the current session bearer token appended as a `?token=…` query parameter, so resources that must be referenced from native HTML attributes (`<img src>`, `<a href>` for downloads / external NOR & SI links) can still authenticate against the API. Unlike `fetchApiAuthenticated`, which puts the token in an `Authorization` header, `authedUrl` exists specifically for the cases where the browser controls the request and you cannot inject a header — image rendering, "Open in new tab" file downloads, anything passed to the platform rather than to `fetch`. Returns the input URL unchanged when there is no token or no URL, so it is safe to call eagerly during render before auth state is hydrated.

## Invariants

- Token is URL-encoded (`encodeURIComponent`) — never paste raw token bytes into a URL string elsewhere and expect it to round-trip.
- Separator selection is purely a `?` vs `&` check on whether `url` already contains a `?`; it does not parse the URL or detect existing `token=` params, so calling `authedUrl(authedUrl(x))` will produce a malformed double-token query.
- Returns the exact input string when `token` is null/empty or `url` is falsy — callers can rely on this for SSR (`window` undefined → `getAuthToken()` returns `null` → identity passthrough) and for public/unauthenticated rendering paths.
- Only meaningful in the browser: `getAuthToken()` short-circuits to `null` under SSR, so any `<img>`/`<a>` rendered server-side will be tokenless and the API must accept the request via a different mechanism (public scope, or hydration-time re-render).
- API side, the partner contract lives in `concorda-api/routers/media.py::serve_file` (and a few peers): they accept `?token=` as a fallback to the `Authorization` header, resolved via `get_current_user_id`. If you change the query parameter name here, change it there.

## Gotchas

- **Token-in-URL is the leakiest place to put a credential**: it lands in browser history, the `Referer` header on outbound links, server access logs, CDN logs, and screenshots/screen-shares. The API explicitly redacts `token=` in its log filter (`main.py::_TOKEN_REDACT_PATTERNS`, alongside the `/api/schedule/feed/<token>.ics` and `/api/invite/<token>` patterns) — keep that filter in sync if the param name ever changes.
- Used on `regatta.links.nor_url` / `si_url` in `members/regattas/page.tsx` and via `LinkSlot` in `regatta-detail-sections.tsx`. These can be **arbitrary external URLs** (sailing-instruction PDFs hosted on club sites). Appending our session token to a third-party domain leaks it via `Referer` on the off-site request. There is no allowlist or same-origin check here — worth revisiting; today the assumption is that NOR/SI links are typically internal `/api/media/serve/...` paths, but nothing enforces that.
- The token expires (default session lifetime in `AuthToken`); a long-lived rendered page can hold stale `<img src>` attributes that will start 401-ing without the React tree re-rendering. There is no expiry-aware refresh — consumers either tolerate broken images on long-idle tabs or remount.
- Not idempotent across calls if the token rotates: each render re-reads `localStorage`, so an `<img>` whose `src` is recomputed after re-login will silently switch tokens. Image caches keyed on URL will see this as a different resource.
- Webcal / ICS subscriptions do **not** use this helper. They use a separate, long-lived per-user feed token baked into the path (`/api/schedule/feed/<token>.ics`) so calendar clients can poll without a session. Don't conflate the two — `authedUrl` is session-scoped, the feed token is not.

## Cross-cutting concerns

- Auth model: piggybacks on `localStorage["auth_token"]`, the same bearer used by `fetchApiAuthenticated`. Anything that invalidates the session token (logout, password change, token rotation) invalidates already-rendered URLs.
- Rate limiting: the in-memory rate limiter in `auth.py` keys on token; image-heavy pages can spike request counts fast since each `<img>` is a separate authenticated request.
- DB pool: the partner endpoint `/api/media/serve` was specifically restructured (incident 2026-05-06) to release its DB session before streaming, because authed image loads can park a pool slot for the entire download. If you add new `authedUrl` consumers that fetch large blobs, verify the server endpoint follows that same release-early pattern.
- Audit/logging: token redaction is centralized in `main.py`; do not log raw URLs that flowed through `authedUrl` from elsewhere.

## External consumers

None known. The query-param token contract is consumed by browser-rendered HTML in `concorda-web` only. The Expo iOS app uses `Authorization` headers via `fetchApiAuthenticated` and does not call this. Calendar clients (Google/Apple) use the separate webcal feed-token URL, not this helper. Webhooks/scheduled jobs do not render UI and do not depend on it.

## Open questions

- Should `authedUrl` refuse to append the token when the URL is cross-origin? The NOR/SI link case suggests yes, but a same-origin check would also need to handle the relative-path form (`/api/media/...`) consumers actually pass.
- Is there appetite to migrate to short-lived signed URLs (HMAC over path+expiry) instead of bearer-token-in-query, which would close the leakage and expiry issues at once? The media router already has the seam for it.
- Should the helper detect an existing `token=` param and replace rather than double-append, to make it safe to compose?
