// Module of helper functions; bundled and re-exported as a namespace by
// the barrel below. Mirrors the canonical "utility module" shape (zod's
// `core/util.ts`, lodash sub-modules, etc.).
export function pad(s: string, n: number): string {
  return s.padStart(n, " ");
}

export function snake(s: string): string {
  return s.replace(/[A-Z]/g, (c) => "_" + c.toLowerCase());
}
