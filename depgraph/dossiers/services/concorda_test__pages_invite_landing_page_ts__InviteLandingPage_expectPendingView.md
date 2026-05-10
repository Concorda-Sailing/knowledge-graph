---
node_id: concorda-test::pages/invite-landing.page.ts::InviteLandingPage.expectPendingView
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 026851c82693daccf165e1ca57a3e5d293b1993f48a57889cc5ae9f5f41c0dc5
status: llm_drafted
---

# InviteLandingPage.expectPendingView

## Purpose

Verifies that the user is on the correct landing page after clicking an invite link but before completing the onboarding/acceptance flow. It specifically asserts that the boat name heading is visible to confirm the user has landed on the correct context-specific page. This is used to distinguish between a successful redirect to the "pending" state versus an error state or a successful "accepted" state.

## Invariants

- **Requires a `boatNameFragment`** — the method expects a string representing a portion of the boat's name to verify the heading.
- **Uses a 10s visibility timeout** — `this.boatNameHeading` must be visible within 10,000ms to pass.
- **Strictly verifies the heading** — it performs a two-step check: first the general heading visibility, then a specific text match for the `boatNameFragment`.

## Gotchas

- **Regex-based text matching** — the `acceptedPanel` locator uses a regex `/you.?re on the crew/i` to handle the escaped apostrophe (`&apos;`) in the "You're on the crew!" string. If the UI text changes to use a standard apostrophe or different phrasing, this locator will fail.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
