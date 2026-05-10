---
node_id: concorda-web::src/components/boat/boat-positions-config.tsx::positionsFromApi
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 88339fad8a885e1e2d7567be746aa5e7d981e00055a9b9201dff2b883c884e25
status: llm_drafted
---

# positionsFromApi

## Purpose

Converts an array of `BoatConfigPosition` objects from the API into a `Map<string, number>` for easier manipulation in the UI. This is a data-shaping utility used to bridge the gap between the flat, structured API response and the Map-based state used by the `BoatPositionsConfig` component.

## Invariants

- **Input is an array of `BoatConfigPosition` objects.** Each object must contain a `name` and a `count`.
- **Returns a `Map<string, number>`.** The map keys are the position names, and values are the counts.
- **Default count is 1.** If `p.count` is null or undefined, the function defaults the value to `1` via `p.count ?? 1`.
- **The map is a fresh instance.** Every call returns a new `Map` object.

## Gotchas

- **Implicit count handling.** Because of the `p.count ?? 1` logic, a position with a count of `0` in the API might be interpreted as `1` if the API returns `null` or `undefined` for that field.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: None.
- **Rate limit**: None.
- **Side effects**: Used by `seedDefaultConfigs` in `BoatPositionsConfig` to transform local `PRESETS` into API-ready objects via `positionsToApi`.

## External consumers

None known.
