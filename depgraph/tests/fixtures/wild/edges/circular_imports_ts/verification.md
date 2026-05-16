## Prediction (written before running extractor)

### Pattern
`a.ts` imports `greet` from `./b.js`; `b.ts` imports `hello` from `./a.js`. Circular.

### Expected behavior
ts-morph resolves module specifiers using the project's source files.
With circular imports, ts-morph may handle this gracefully (TypeScript's type checker
supports circular imports) or may produce partial results. Key question: does the
TS extractor crash on circular imports?

No crash expected — ts-morph builds the full project graph before resolution.

### Import resolution
`a.ts: import { greet } from "./b.js"`:
- ts-morph resolves `./b.js` → `src/b.ts` (extension mapping)
- `symByPath["src/b.ts"]["greet"]` = `fixture::src/b.ts::greet`
- Edge: a.ts imports `fixture::src/b.ts::greet` (exact)

`b.ts: import { hello } from "./a.js"`:
- ts-morph resolves `./a.js` → `src/a.ts`
- `symByPath["src/a.ts"]["hello"]` = `fixture::src/a.ts::hello`
- Edge: b.ts imports `fixture::src/a.ts::hello` (exact)

### Call edges
`hello` in a.ts calls `greet("world")`:
- importsByPath["src/a.ts"]["greet"] = fixture::src/b.ts::greet
- Emits `calls -> fixture::src/b.ts::greet` (exact)

`callBack` in b.ts calls `hello()`:
- importsByPath["src/b.ts"]["hello"] = fixture::src/a.ts::hello
- Emits `calls -> fixture::src/a.ts::hello` (exact)

### Predicted edges
- src/a.ts (module): imports fixture::src/b.ts::greet (exact)
- src/b.ts (module): imports fixture::src/a.ts::hello (exact)
- hello: calls fixture::src/b.ts::greet (exact)
- callBack: calls fixture::src/a.ts::hello (exact)
