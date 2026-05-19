// In-corpus module — `import * as util from "./util.js"` should turn
// `util.greet()` into an edge that points back at this file's exports.
export function greet(): string { return "hi"; }
export function farewell(): string { return "bye"; }
