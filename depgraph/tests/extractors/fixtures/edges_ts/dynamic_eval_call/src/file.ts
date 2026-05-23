// `eval(...)` — issue #90. Structurally a bare-name call, semantically
// pure dynamic dispatch.

export function runDynamic(src: string) {
  return eval(src);
}
