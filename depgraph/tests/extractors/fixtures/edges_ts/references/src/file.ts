let globalCount = 0;
export function reader(): number {
  return globalCount;
}
export function writer() {
  globalCount = 1;
}

// Property-name shadowing: `globalCount` here is a property of an object
// literal, not a read of the module-scope var. Without the guard the
// extractor emits a spurious `reads` edge.
export function propertyKey() {
  return { globalCount: 42 };
}

// Property access: `obj.globalCount` — the `.globalCount` is the
// property name on `obj`, not a read of the module-scope var.
export function propertyAccess(obj: { globalCount: number }) {
  return obj.globalCount;
}

// Parameter shadowing: parameter named the same as a module-scope var.
// The Identifier at the parameter declaration site is a name slot, not
// a read. Scope tracking (#82) also suppresses the body read since
// `globalCount` here resolves to the parameter, not the module var.
export function parameterShadow(globalCount: number) {
  return globalCount;
}

// Destructuring binding: `const { globalCount }` creates a local
// binding; the Identifier at the binding site is a name slot. Scope
// tracking (#82) suppresses the subsequent body read for the same
// reason as the parameter case above.
export function destructureBinding(obj: { globalCount: number }) {
  const { globalCount } = obj;
  return globalCount;
}

// Shorthand property assignment: `{ globalCount }` IS a real read of
// the module-scope var (the value comes from scope, not the literal).
export function shorthandRead() {
  return { globalCount };
}

// #82: parameter shadowing under a distinct module var so the test is
// independent of the parameterShadow case above. Body's `value` is the
// parameter, not the module-scope `value`; no reads edge should target
// ::value.
let value = 0;
export function paramShadow(value: number): number {
  return value + 1;
}

// #82: destructure-binding shadowing — `const { label } = src` introduces
// a local; the subsequent `return label` reads the local, not the module
// `label`. The destructure source is typed via an interface declared
// outside the function so the type annotation doesn't itself contain a
// PropertySignature named `label`.
let label = "outer";
interface LabelHolder { label: string }
export function destructureShadow(src: LabelHolder): string {
  const { label } = src;
  return label;
}
