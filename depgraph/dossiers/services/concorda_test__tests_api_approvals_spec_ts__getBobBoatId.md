---
node_id: concorda-test::tests/api/approvals.spec.ts::getBobBoatId
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6b06cb32933616baac1a19247e51f9c76a2d47162eb0eaaf00962ebd519ecd31
status: llm_drafted
---

# getBobBoatId

## Purpose

A test helper that retrieves the unique identifier for the boat named `BOATS.testBreeze.name`. It abstracts the multi-step process of authenticating as `bobClient`, fetching the full list of boats, and searching for the specific boat instance. It is used to ensure that tests involving the "Approvals API" have a valid target ID for boat-related operations like co-owner promotions.

## Invariants

- **Returns a `string`** representing the boat's UUID.
- **Requires a successful `bobClient()` authentication** to fetch the boat list.
- **Throws an error if the boat name does not exist** in the current test environment's seed data.

## Gotchas

- **Cumulative-state dependency:** If a prior test run leaves a user (like Carol) as a co-owner of the boat, subsequent tests in the same suite may fail. Per commit `8644b3d`, the test suite must explicitly remove the `BoatCrew` member (e.g., via `bob.removeCrewMember`) to reset the state before attempting a new co-owner request.
- **Strict name matching:** The function relies on `BOATS.testBreeze.name` being present in the seeded database. If the seed data is not refreshed or if the name is changed in the `BOATS` constant, this helper will throw.

## Cross-cutting concerns

- **Auth**: Uses `bobClient()` which relies on `api.login(USERS.bob.email, USERS.bob.password)`.
- **Side effects**: The tests using this helper (specifically the `create → list → vote approve flow`) modify the `BoatCrew` and `ApprovalRequest` state, which can cause subsequent runs to fail if the "Carol" co-owner state is not cleaned up.

## External consumers

None known.
