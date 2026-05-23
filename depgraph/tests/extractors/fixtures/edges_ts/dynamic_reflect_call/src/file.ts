// Dynamic dispatch via Reflect — issue #90.
// `Reflect.get(obj, name)(...)` returns a value off `obj`; calling it is
// dynamic dispatch. `Reflect.apply(fn, ...)` is an explicit dynamic call.

export function dispatchGet(obj: unknown, name: string) {
  return (Reflect.get(obj as object, name) as () => unknown)();
}

export function dispatchApply(fn: Function, thisArg: unknown, args: unknown[]) {
  return Reflect.apply(fn, thisArg, args);
}
