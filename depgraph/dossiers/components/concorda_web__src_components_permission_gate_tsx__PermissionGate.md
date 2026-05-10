---
node_id: concorda-web::src/components/permission-gate.tsx::PermissionGate
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a3bb564b71fd4c5fdcbde2a5913100649b4d9bc861628ddad4734fd71e19ee00
status: llm_drafted
---

# PermissionGate

## Purpose

A UI wrapper used to conditionally render content based on the current user's permission set. It accepts either a single permission string or an array of strings and checks them against the `user.permissions` array retrieved from `useAuth()`. Use this instead of manual conditional rendering when you want to provide a standardized "Access Denied" UI state for unauthorized users.

## Invariants

- **Requires `useAuth` context.** The component relies on the `user` object and `isLoading` state from the authentication hook.
- **Input is polymorphic.** The `permission` prop can be a single `string` or a `string[]`.
- **Returns `null` during loading.** If `isLoading` is true, the component renders nothing to prevent flickering the "Access Denied" state while the session is being established.
- **Fallback UI is a centered Card.** If the user lacks the required permission, it renders a `ShieldAlert` icon and a link to `/members`.

## Gotchas

- **`isLoading` state is critical.** If the `useAuth` hook does not correctly set `isLoading` to true during the initial session fetch, users may see the "Nothing to See Here" screen briefly before the user object populates.

## Cross-cutting concerns

- **Auth**: Directly depends on `useAuth` to access the `user.permissions` array.
- **Side effects**: Used to guard sensitive UI sections like administrative settings or premium feature access.

## External consumers

None known.
