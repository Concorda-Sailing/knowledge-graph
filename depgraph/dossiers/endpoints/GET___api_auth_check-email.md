---
node_id: GET::/api/auth/check-email
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bea1d23875188cd3876479b6dd35886970f559e93680ab5fdab806f30f5f7b89
status: llm_drafted
---

# GET /api/auth/check-email

## Purpose

Provides a way to check if an email address is already registered in the system before a user attempts to sign up or log in. This prevents unnecessary friction by allowing the UI to signal availability or existing account status. It is distinct from the `/register` endpoint, which actually creates the `Person` record.

## Invariants

- **Method/Path**: `GET /api/auth/check-email`
- **Input**: Requires a single `email` query parameter.
- **Return Shape**: Returns a JSON object with a boolean field `{"available": true | false}`.
- **Case Insensitivity**: The check is performed by converting the input email to lowercase and stripping whitespace to match the `Person.email` storage convention.

## Gotchas

- **Origin/Referer Enforcement**: In production, the request must originate from an allowed domain (checked via `_EMAIL_CHECK_ALLOWED_ORIGINS`). If the `origin` or `referer` headers are missing or incorrect, the endpoint returns a `403 Forbidden`.
- **Rate Limiting**: This endpoint is heavily throttled to prevent enumeration-based scraping. It uses a burst limit (1 request per second) and a daily limit (10 requests per 24 hours) per client IP.
- **Test Environment Bypass**: Per commit `543b02d`, the origin allowlist check is bypassed when `CONCORDA_ENV=test`. This allows Playwright/integration tests to run without spoofing headers.

## Cross-cutting concerns

- **Auth**: None (public endpoint).
- **Rate limit**: Uses `_email_check_rate_limit` with a 24h window and a 1s burst interval.
- **Side effects**: None.

## External consumers

- `concorda-web::src/lib/api.ts::authApi.checkEmail`
