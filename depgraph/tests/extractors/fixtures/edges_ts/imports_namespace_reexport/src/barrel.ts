// Barrel module — re-exports helpers as a namespace.
//
// The `export * as helpers from "./helpers.js"` form binds a new name
// (`helpers`) in this module's exports, but doesn't itself introduce
// any class/function/variable primitive. Without #89's fix, the
// consumer's `import { helpers } from "./barrel.js"` produces an
// `imports` edge to `<barrel.ts>::helpers` that orphans (no primitive
// at that id).
export * as helpers from "./helpers.js";
