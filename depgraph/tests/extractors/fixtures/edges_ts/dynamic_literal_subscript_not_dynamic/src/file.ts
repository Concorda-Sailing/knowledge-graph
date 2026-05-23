// Negative for #90: `obj["literal"]()` with a string-literal key is
// structurally resolvable in principle — do NOT classify as dynamic.

export function callLiteral(registry: Record<string, () => void>) {
  return registry["doit"]();
}
