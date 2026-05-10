---
node_id: concorda-test::scripts/staging-signup.ts::attachListeners
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9622fe65553e6ee3197146c103d60ee479a80fde24183c8565efff33b7e3bcdc
status: llm_drafted
---

# attachListeners

## Purpose

Attaches event listeners to a Playwright `Page` instance to capture and aggregate errors during the staging signup flow. It populates a `Findings` object with console errors, page crashes, and API failures to ensure that E2E tests can report failures that don't necessarily trigger a hard test timeout.

## Invariants

- **Captures only API errors** — The `page.on('response')` listener filters for `status >= 400` and ensures the URL includes `/api/` to avoid flagging static asset failures (e.g., 404s on images).
- **Mutates the `findings` object** — It does not return a value; it pushes error strings and objects directly into `findings.consoleErrors`, `findings.pageErrors`, and `findings.networkErrors`.
- **Filters noise** — The `console` listener explicitly ignores `[Fast Refresh]` and `Download the React DevTools` messages to prevent false positives in test reports.

## Gotchas

- **Email confirmation requires keyboard typing** — Per the logic in `fillInfoStep` (lines 107-109), the `confirmEmail` field blocks standard `fill()`/paste actions; the agent must use `page.keyboard.type()` to successfully complete the signup flow.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
