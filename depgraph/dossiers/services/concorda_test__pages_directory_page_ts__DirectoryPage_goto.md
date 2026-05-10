---
node_id: concorda-test::pages/directory.page.ts::DirectoryPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ec02cb85b5e9d308a287c1112830249b978d55561838a6dcd9ec5aa9fa4cd082
status: llm_drafted
---

# DirectoryPage.goto

## Purpose

Navigates the Playwright browser to the `/members/directory` endpoint. It is the primary entry point for any E2E test that needs to interact with the member list, such as verifying search results or alphabetical filtering.

## Invariants

- **Navigates to `/members/directory`** — the hardcoded path is the single source of truth for the directory URL.
- **Waits for `networkidle`** — the method ensures the page is fully loaded and network activity has subsided before returning control to the test.
- **Requires an active session** — because it navigates to a protected route, the `ApiClient` or `LoginPage` must have established a session prior to calling this.

## Gotchas

- **Initial scaffolding only** — per commit `fd0c570`, this is part of the initial E2E suite scaffolding; the directory page structure and its locators (like `memberRows` or `paginationInfo`) are currently being established and may be unstable as the test suite matures.

## Cross-cutting concerns

- **Auth**: Requires a valid session/auth state to be present; otherwise, the navigation will likely redirect to a login page or return a 401/403.
- **Side effects**: Tests using this method are part of the `concorda-test` E2E suite, which relies on the underlying API and database state being correctly seeded.

## External consumers

None known.
