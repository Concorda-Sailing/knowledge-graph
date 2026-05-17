# Verification log: chained_reexports_ts

## Pre-read prediction

Without the fix: orphan edges from `consumer.ts` and (depending on which branch
handles it) possibly from the barrel itself, because the re-export emission
branch in `attachImportsEdges` (extract.ts) only consults `symByPath` and falls
back to `${repoKey}::${targetRel2}::${exportedName}` when the symbol isn't
locally defined in the immediate target file.

With the fix: the re-export map is closed under transitive lookup, and both
emission branches consult the closed map. All three expected edges resolve to
`fixture::src/definer.ts::realFunc`.

## Prediction vs expected.json

Matches the fix-applied state.

## Notes

The `calls` edge from `useFunc` is exact because intra-function type binding
resolves through the imports map; that map already uses the closed re-export
resolution, so calls land on the correct primitive.
