---
node_id: concorda-web::src/app/members/setup/page.tsx::SetupPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 82faeb774e0029fb68d0af05ad2e912c988b41bbe3b9c415f0daa4731ad6bf10
status: llm_drafted
---

# SetupPage

## Purpose

The onboarding wizard for new members to complete their profiles. It manages a multi-step state machine (`WizardStep`) that directs users through boat details, sailing resumes, and racing preferences. It is distinct from the standard profile edit page because it includes aggressive auto-save logic via debounced timers to ensure progress is captured during the onboarding flow.

## Invariants

- **Initial step is conditional** — Users with `grants_boat_management` are routed to `boat-details`, while others start at `sailing-question`.
- **Auto-save is debounced** — `boatSaveTimer` and `resumeSaveTimer` use `setTimeout` to prevent API flooding during rapid typing.
- **Boat updates require a `sail_number`** — The `autoSaveBoat` function returns early without calling `profileApi.updateBoat` if `form.sail_number` is missing.
- **Form state is local** — The wizard manages its own `useState` for form data and `useRef` for form handles, syncing to the backend via `profileApi`.

## Gotchas

- **Navigation redirect logic** — Per commit `679fe81`, the setup wizard navigation and `?tab=boat-*` URL redirects must be carefully managed to ensure users don't get stuck in a loop or land on an empty step.
- **Silent failures in auto-save** — The `autoSaveBoat` function uses a `try/catch` that swallows errors (`/* silent */`). If a user's boat update fails, they will not receive a toast notification, making it difficult to know if their progress was actually persisted.
- **Manual float conversion** — `autoSaveBoat` explicitly casts `length` and `draft` to floats. If the API expects strings or different precision, this conversion is the point of failure.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to determine `canManageBoats` and the starting step.
- **Side effects**: Updates to boat details via `profileApi.updateBoat` will reflect in the "boat-finder" and "crew-finder" components once the user's profile is refreshed.

## External consumers

None known.

## Open questions

- The `autoSaveBoat` function currently swallows all errors. Should we implement a non-silent error state or a toast notification for failed auto-saves to improve UX during onboarding?
