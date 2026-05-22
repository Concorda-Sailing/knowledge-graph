// A `$constructor`-style binding is a `variable` primitive: the call shape
// returns a class-like callable, and TS code does `new Factory(...)` against
// it. Real-world example: zod's `export const ZodObject = core.$constructor(
// "ZodObject", (inst, def) => { ... })` (a variable) consumed as
// `return new ZodObject(def)` inside its factory functions.
//
// The interface declaration below mirrors the wild shape: zod's
// `schemas.ts` declares `interface ZodObject<...> extends ... {}` alongside
// the const binding. The two primitives collide on canonical id, so
// reconcile's `by_id` resolves the target's kind to whichever entry comes
// last (the variable, since it appears below the interface).
//
// Without the fix: `instantiates -> variable` at confidence=exact, which the
// reconcile validator rejects per EDGE_KIND_RULES (instantiates.target =
// [class]). With the fix: instantiates is emitted at confidence=fuzzy, and
// the taxonomy permits variable / function targets ONLY under fuzzy
// confidence (#88).

export interface Factory {
  name(): string;
}

function makeFactory() {
  return class {
    name(): string {
      return "made";
    }
  };
}

export const Factory = makeFactory();

export function makeOne() {
  return new Factory();
}
