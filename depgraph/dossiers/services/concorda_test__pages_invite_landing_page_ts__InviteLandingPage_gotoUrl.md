---
node_id: concorda-test::pages/invite-landing.page.ts::InviteLandingPage.gotoUrl
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4f54d140905d94eaf8172996c4f32b8f157978053409c3a520c976facdf9ccdc
status: current
---

# InviteLandingPage.gotoUrl

## Purpose

The primary navigation method for the Invite Landing Page. It directs the Playwright browser to a specific URL, typically an invite link containing a unique token (e.g., `/invite/{token}`). This serves as the entry point for testing the transition from an unauthenticated/unlogged state to the "You're on the crew!" state.

## Invariants

- **Accepts a single string argument.** The `url` must be the full path or absolute URL to the landing page.
- **Returns `Promise<void>`.** It is a side-effect-only method that navigates the browser instance.
- **Relies on the `page` instance.** It uses the underlying Playwright `Page` object to perform the navigation.

## Gotchas

- **Regex-based error detection.** The `errorText` locator uses a regex that captures multiple failure modes: `"invite link is invalid|already been used|invite not found"`. If the API or frontend changes the wording of these error messages, `expectErrorView()` will fail to find the text.
- **Apostrophe rendering.** The `acceptedPanel` locator looks for the string `/you.?re on the crew/i`. This is specifically designed to handle the `&apos;` rendering in the DOM to avoid brittle text matching.

## Cross-cutting concerns

- **Auth**: This is the entry point for unauthenticated users. Success in this flow typically leads to a state where the user must then interact with `logInButton` or `acceptButton` to establish a session.
- **Side effects**: Successful navigation and subsequent `accept()` calls drive the state transition for the user's invitation status in the database.

## External consumers

None known.
