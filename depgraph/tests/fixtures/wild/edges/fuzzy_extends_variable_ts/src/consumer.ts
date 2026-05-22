// A class declared via a const factory binding is a `variable` primitive
// (not a `class`). Real TS codebases ship parameterized / mixin base classes
// this way — e.g. `const ZodType = createZodType(...)` then
// `class ZodString extends ZodType { ... }` in another module.
//
// Without the fix: `extends -> variable` at confidence=exact, which the
// reconcile validator rejects per EDGE_KIND_RULES (extends.target = [class]).
// With the fix: extends is emitted at confidence=fuzzy, taxonomy is updated
// to allow variable targets ONLY under fuzzy confidence (#86).

function makeBase() {
  return class {
    tag(): string {
      return "base";
    }
  };
}

export const Factory = makeBase();

export class Child extends Factory {
  named(): string {
    return this.tag() + ":child";
  }
}
