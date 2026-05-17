# Verification log: wildcard_reexport_ts

## Pre-read prediction

Without the fix: imports of `Gadget`/`Tool` orphan onto `barrel.ts::Gadget`/`barrel.ts::Tool`; `instantiates` edge from `build` to `Tool` lands on the placeholder.

With the fix: all three edges resolve to the `types.ts` primitives.

## Prediction vs expected.json

Matches the fix-applied state.

## Notes

The `Gadget` interface produces a class-primitive in the TS extractor today (interfaces and classes share the class-primitive shape). The expected edge target reflects that.
