---
node_id: concorda-web::src/app/members/crewfinder/contact-dialog.tsx::ContactDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8114bb7e98502724eebcd2510f5adf7d146d71be0ebd60ced221a363297b1c9e
status: llm_drafted
---

# ContactDialog

## Purpose

Provides a modal interface for users to send a direct message to a specific person (crew) or entity (boat) within the Crewfinder module. It abstracts the complexity of the `crewfinderApi.contact` call, managing local state for the message body, loading states, and error handling. Use this instead of building custom textareas when a user needs to initiate contact from a profile or detail view.

## Invariants

- **`contactType` must be either `"crew"` or `"boat"`** to satisfy the API requirement.
- **`targetId` is the unique identifier** for the recipient (user ID or boat ID).
- **`message` is trimmed before transmission** to prevent empty-string submissions via whitespace.
- **`onOpenChange` is guarded by `sending` state**; the dialog will not close via clicking the backdrop or pressing escape while a request is in flight.
- **`MAX_MESSAGE_LENGTH` limits input** via the `onChange` handler to prevent oversized payloads.

## Gotchas

- **`onOpenChange` side effects**: If the user clicks outside the dialog or presses escape while `sending` is true, the `onOpenChange` call is intercepted to prevent the UI from closing and losing the message state mid-request.
- **`DEFAULT_MESSAGES` dependency**: The component relies on a constant `DEFAULT_MESSAGES` keyed by `contactType`. If a new `contactType` is added to the props but not the constant, the message field will be empty on open.

## Cross-cutting concerns

- **Auth**: Relies on `crewfinderApi.contact`, which requires a valid session/bearer token (see `ApiClient` patterns).
- **Side effects**: Successful submission triggers a `toast` notification to confirm delivery to the user.

## External consumers

None known.
