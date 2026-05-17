# Verification log: default_export_resolution_ts

## Pre-read prediction

Without the fix: orphan import edge to `lib.ts::default`; instantiates edge from `makeWidget` lands on the same placeholder.

With the fix: both edges resolve to `lib.ts::Widget` via the default-export alias map built alongside the re-export map.

## Prediction vs expected.json

Matches the fix-applied state.

## Notes

The `instantiates` edge's `confidence: exact` is preserved because the intra-function type-binding pass consults the imports map, which now contains the correct target.
