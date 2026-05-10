---
node_id: concorda-api::models/organization_event.py::OrganizationEvent
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 532691179f411cc621fc7567e756be86f071792439f26993d7ae913352c576e7
status: llm_drafted
---

# OrganizationEvent

## Purpose

The `OrganizationEvent` model represents a discrete occurrence or state change within a specific organization's context. It is used to track structured data (via the `description` JSON field) that doesn't fit into the standard domain models like `CrewPool` or `TemporalProductMerchandise`. Use this model when you need to record a history of events that are scoped to an organization but require flexible, schema-less metadata.

## Invariants

- **`organization_uuid` and `event_uuid` are mandatory.** Both must be valid 36-character UUID strings.
- **`relationship` is a required string.** It defines the type of event (e.g., "crew_update", "membership_change") and has a maximum length of 50 characters.
- **`description` is a JSON object.** It is a nullable dictionary used to store event-specific metadata.
- **Inherits from `BaseModel`.** The `__init__` method automatically sets the `type` attribute to `"OrganizationEvent"`.

## Gotchas

- **Multi-OA support requirement.** Per commit `fdc87b4`, this model is part of the "events multi-OA" (Organization/Account) feature set, meaning events must be strictly scoped to an organization to prevent cross-tenant data leakage in multi-tenant workflows.

## Cross-cutting concerns

- **Auth**: Scoped by `organization_uuid`; ensure the requesting user has access to the specific organization.
- **Audit**: Acts as a record of truth for organizational state changes.
- **Side effects**: Drives the "my-schedule" series and "crew workflow" logic mentioned in `fdc87b4`.

## External consumers

None known.
