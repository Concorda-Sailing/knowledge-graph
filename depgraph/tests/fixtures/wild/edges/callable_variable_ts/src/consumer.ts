// A const initialized to a function reference is a `variable` primitive, not
// a `function`. Calling it bare must NOT produce `calls → variable`.

export function realImpl(x: number): number {
  return x + 1;
}

// `aliased` is a variable holding a function reference.
const aliased = realImpl;

export function caller(): number {
  // Without the fix: `calls → fixture::src/consumer.ts::aliased` (variable),
  // violating EDGE_KIND_RULES["calls"].target = ["function"].
  // With the fix: no `calls` edge is emitted here. The reads pass attributes
  // the relationship as `reads function→variable` separately.
  return aliased(41) + realImpl(1);
}
