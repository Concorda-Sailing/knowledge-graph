// Dynamic dispatch via element-access — issue #90.
// `obj[key]()` where `key` is a runtime value is pure dynamic dispatch.

export function dispatch(registry: Record<string, () => void>, name: string) {
  return registry[name]();
}

export function dispatchOnAny(obj: unknown, name: string) {
  // The `as any` cast is the most common TS shape for "trust me, this is
  // callable" — the element-access is still dynamic.
  return (obj as any)[name]();
}
