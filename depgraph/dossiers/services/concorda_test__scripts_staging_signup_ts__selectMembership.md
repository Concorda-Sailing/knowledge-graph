---
node_id: concorda-test::scripts/staging-signup.ts::selectMembership
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a0841a3afcc9a1c9ae63a626a941d12643cd96d894b13f0fa320b8cda249b2be
status: current
---

# selectMembership

## Purpose

Navigates the staging environment's registration flow to select a specific membership tier. It navigates to the `/join/register` path, waits for the membership cards to be visible, and returns the display name of the selected tier. This is used as a setup step in E2E flows that require a specific membership level (e.g., testing premium-only features) before proceeding to the info-collection step.

## Invariants

- **Input is a `slug` string** that must match the `id` of a membership card in the DOM.
- **Returns a `Promise<string | null>`** containing the text content of the selected membership's name.
- **Requires `STAGING_URL` to be defined** in the environment to construct the navigation path.
- **Uses `page.waitForSelector` with a 10s timeout** to ensure the membership cards have loaded before attempting to select one.

## Gotchas

- **The `confirmEmail` field blocks paste operations.** Per the implementation of `fillInfoStep` (which follows this step in the flow), the user must `click()` the field and use `page.keyboard.type()` to bypass the input restriction.
- **Hardcoded timeouts are used for stability.** The function uses `page.waitForTimeout(300)` after clicking a membership and `500` after clicking "Next" to allow the UI to transition; these are brittle and may fail if the staging environment experiences high latency.

## Cross-cutting concerns

- **Auth**: None (this is a pre-authentication step in the signup flow).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: N/A.

## External consumers

None known.
