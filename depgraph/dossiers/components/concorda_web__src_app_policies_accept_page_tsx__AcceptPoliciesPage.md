---
node_id: concorda-web::src/app/policies/accept/page.tsx::AcceptPoliciesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d0f3687e40ab7d9ca0af4c6472e27a9f13cf8511d58259e4e5c3c6907d39712e
status: current
---

# AcceptPoliciesPage

## Purpose

The mandatory policy acceptance gateway. This page intercepts users who have pending policy updates and prevents access to the main application until all required policies are reviewed and accepted. It fetches pending policies via `policiesApi.getPending()` and redirects the user to a `next` destination (defaulting to `/members`) once the `handleSubmit` call successfully completes.

## Invariants

- **Authentication is mandatory.** If `isAuthenticated` is false, the user is redirected to `/login` with the current path encoded in the `next` parameter.
- **Redirect behavior is deterministic.** If `policiesApi.getPending()` returns an empty array, the user is immediately redirected to the `next` path to prevent a blocking loop.
- **State-driven submission.** The `allAgreed` memo ensures the submit button logic (implied) relies on the `agreed` record matching all `p.id` values in the `policies` array.
- **Post-acceptance refresh.** The `handleSubmit` function must call `await refreshUser()` after the API call to ensure the local auth context reflects the updated user state/permissions.

## Gotchas

- **Redirect loops.** If the `next` parameter is not handled carefully or if the backend does not immediately clear the pending status upon acceptance, users may be trapped in a redirect loop between this page and the destination.
- **Versioned UI requirement.** Per commit `86ff361`, this page is part of the "versioned policy UI"-driven flow, meaning the UI must be able to handle multiple or versioned policy objects without breaking the `agreed[p.id]` lookup.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to check `isAuthenticated` and `authLoading`; redirects to `/login` if unauthenticated.
- **Audit**: Writing acceptance via `policiesApi.accept` triggers an audit log entry (per commit `86ff361`).
- **Side effects**: Successful submission triggers `refreshUser()`, which updates the global user context and potentially unblocks access to the rest of the application.

## External consumers

None known.
