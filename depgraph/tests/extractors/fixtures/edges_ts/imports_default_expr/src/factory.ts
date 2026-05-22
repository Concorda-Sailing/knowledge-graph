// File A — exports a value built from a function call as the default.
// This shape (`export default someFactory(...)`) is the canonical TS
// config-file idiom (vitest.config.ts, next.config.js, etc.) and the
// one #85 caught producing orphan import edges in zod.
function makeThing(name: string) {
  return { name };
}

export default makeThing("widget");
