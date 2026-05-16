let globalCount = 0;
export function reader(): number {
  return globalCount;
}
export function writer() {
  globalCount = 1;
}
