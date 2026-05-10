---
node_id: concorda-web::src/components/ui/chart.tsx::getPayloadConfigFromPayload
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6c2378df4a7cd2bc1cb391078ace0195eca81ff215b6973d80f83d45b55dc113
status: current
---

# getPayloadConfigFromPayload

## Purpose

Extracts the correct configuration object from a chart payload based on a provided key. It is designed to handle nested payload structures where the actual label key might be stored in a top-level property or a nested `payload` object. Use this when mapping data points to `ChartConfig` to ensure the legend or tooltip displays the correct human-readable label.

## Invariants

- **Input `payload` must be an object.** If `payload` is null or not an object, the function returns `undefined`.
- **Key resolution is hierarchical.** It first checks the top-level `key` in the payload, then falls back to a nested `payload.payload` property.
- **Returns a string or undefined.** The function resolves to a `configLabelKey` which is then used to index the `config` object.
- **Fallback behavior.** If the resolved `configLabelKey` does not exist in the `config` object, it defaults to using the original `key` provided in the arguments.

## Gotchas

- **Nested payload structure.** The function specifically looks for a `payload.payload` pattern (lines 329-334). This is a common pattern in certain charting libraries where the data point is wrapped in an extra layer of metadata.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
