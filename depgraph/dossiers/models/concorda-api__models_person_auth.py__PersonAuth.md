---
node_id: concorda-api::models/person_auth.py::PersonAuth
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2c26c6c5267ade25c5ef19e8d6abb6b46c4da9c8aa7488c10b38b45afbf57ada
status: llm_drafted
---

# PersonAuth

## Purpose

The `PersonAuth` model stores the core authentication credentials and identity linkage for a user. It acts as the bridge between standard email/password authentication and OAuth providers. It is distinct from the `Person` model (which handles profile/identity data) by focusing strictly on the security-sensitive fields required for session establishment.

## Invariants

- **`person_uuid` is the primary identifier** and must be a 36-character string.
- **`person_uuid` is unique** and indexed to ensure one-to-one mapping between a person and their auth credentials.
- **`oauth_provider` and `oauth_id` are nullable** to support both OAuth-based and local password-based login flows.
- **`email_verified` defaults to `False`** to prevent unverified accounts from accessing protected resources.

## Gotchas

- **Schema redesign impact**: Per commit `ee82e42`, this model was part of a significant schema redesign involving new relationship tables and data migrations. Any changes to the `person_uuid` format or the addition of new OAuth providers must be coordinated with the migration scripts to avoid breaking the identity-linkage logic.

## Cross-cutting concerns

- **Auth**: Primary source of truth for the `POST /api/auth/login` flow and OAuth callback verification.
- **Audit**: Changes to `password_hash` or `email_verified` status are critical security events.

## External consumers

None known.
