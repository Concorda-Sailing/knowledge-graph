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
// a read.
export function parameterShadow(globalCount: number) {
  return globalCount;
}

// Destructuring binding: `const { globalCount }` creates a local
// binding; the Identifier at the binding site is a name slot.
export function destructureBinding(obj: { globalCount: number }) {
  const { globalCount } = obj;
  return globalCount;
}

// Shorthand property assignment: `{ globalCount }` IS a real read of
// the module-scope var (the value comes from scope, not the literal).
export function shorthandRead() {
  return { globalCount };
}
