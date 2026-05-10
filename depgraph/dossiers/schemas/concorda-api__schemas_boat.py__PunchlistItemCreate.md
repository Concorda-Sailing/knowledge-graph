---
node_id: concorda-api::schemas/boat.py::PunchlistItemCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 501b7e2d000071c9d780aa67a8b3d8b933af320ebb361308002f2025c60e15d9
status: llm_drafted
---

# PunchlistItemCreate

## Purpose

The Pydantic model for creating a new item in a boat's punchlist. It defines the required payload for the `POST /api/boats/{boat_uuid}/punchlist` endpoint. Use this instead of `PunchlistItemUpdate` when initializing a new task, as it enforces the presence of a `title`.

## Invariants

- **`title` is required.** Unlike the update model, this field cannot be omitted during creation.
- **`importance` defaults to `"medium"`.** Valid values are `"high"`, `"medium"`, or `"low"`.
- **`assigned_to_uuid` is optional.** A task can be created without an assignee.

## Gotchas

- **`importance` is a string, not an Enum.** While the docstring suggests specific values, the type is a raw `str`. If a developer expects a strict Enum validation, they may be surprised by the lack of runtime enforcement for values outside the high/medium/low set.

## Cross-cutting concerns

- **Auth**: Handled by the `POST /api/boats/{0}/punchlist` router.
- **Side effects**: Creating an item via this schema triggers updates to the boat's punchlist state.

## External consumers

- None known.
