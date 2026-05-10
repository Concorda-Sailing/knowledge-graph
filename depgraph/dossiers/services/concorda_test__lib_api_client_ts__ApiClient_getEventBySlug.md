---
node_id: concorda-test::lib/api-client.ts::ApiClient.getEventBySlug
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 21d62e01046d217a81866d8056dd4657d78507e94879290f64fa0ec24a5c7cbb
status: current
---

# ApiClient.getEventBySlug

## Purpose

Fetches detailed event data using a unique string identifier (slug). This is the primary method for retrieving a single event's full profile when the UI or a test needs to transition from a list view (where only slugs or IDs are present) to a detailed view.

## Invariants

- **HTTP Method**: Performs a `GET` request.
- **Endpoint Path**: Targets `/api/events/slug/${slug}`.
- **Return Shape**: Returns a `Promise<Record<string, unknown>>` representing the event object.
- **Slug Uniqueness**: Assumes the provided `slug` is a unique, URL-safe identifier for the specific event.

## Gotchas

- **Auth Dependency**: Requires a valid bearer token in the `ApiClient` instance. If the token is missing or expired, this will return a 401/403, which can break E2E flows that rely on `getEventBySlug` to populate detail pages.
- **Test Host Connectivity**: Per commit `917acfe`, the API client is configured to point at a remote test host. Ensure the environment is correctly configured so that the slug resolution happens against the intended test instance rather than a local dev server.

## Cross-cutting concerns

- **Auth**: Depends on the bearer token established via `ApiClient.login` or `setToken`.
- **Side effects**: Used by tests that verify the "Event Detail" view after navigating from a list or a search result.

## External consumers

None known.
