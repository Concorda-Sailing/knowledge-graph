---
node_id: concorda-web::src/components/profile/membership-upgrade.tsx::MembershipFeatures
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 91d567cc54d5a7c2bb3005ef6f395fc35a3de898673cf79836d37ad608bb3ec5
status: llm_drafted
---

# MembershipFeatures

## Purpose

Renders the visual feature list for a specific membership tier. It maps the boolean flags from a `TemporalProductPublic` object (e.g., `grants_crewfinder`, `grants_boat_management`) to a list of labels with visual indicators (checkmarks or strikethroughs). This is a stateless presentation component used within the larger `MembershipUpgrade` flow to show users what they currently have access to versus what they might gain by upgrading.

## Invariants

- **Input is a `TemporalProductPublic` object.** The component relies on the `plan` prop to determine which features are "included."
- **Features are hardcoded to the product schema.** The labels (e.g., "Crew Finder", "Boat Management") must match the semantic meaning of the `grants_` boolean flags on the `plan` object.
- **Visual state is binary.** A feature is either fully included (green check, no strikethrough) or not included (muted text, strikethrough).

## Gotchas

- **Membership requirements are strictly enforced for co-owners.** Per commit `47688ac`, the system now requires a "Boat Owner" membership to accept co-owner invites; ensure any feature-flag logic related to ownership permissions remains tightly coupled to these specific product tier grants to avoid unauthorized access.

## Cross-cutting concerns

- **Auth**: Relies on the `profile` and `plan` data fetched via `temporalProductsApi` and `paymentsApi`.
- **Side effects**: Changes to the membership plan (via the parent `MembershipUpgrade` component) will trigger a re-render of this list to reflect new feature availability.

## External consumers

None known.
