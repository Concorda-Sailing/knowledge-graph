// Fixture: overload_storm
// Tests: only the implementation signature emits a primitive; overload declarations are skipped.

// Standalone function: 5 overload declarations + 1 implementation
export function parse(input: string): number;
export function parse(input: number): number;
export function parse(input: boolean): number;
export function parse(input: string[]): number;
export function parse(input: null): number;
export function parse(input: unknown): number {
  if (typeof input === "string") return parseInt(input, 10);
  if (typeof input === "number") return input;
  if (typeof input === "boolean") return input ? 1 : 0;
  if (Array.isArray(input)) return input.length;
  return 0;
}

// Class with overloaded constructor and overloaded method
export class Formatter {
  constructor(locale: string);
  constructor(locale: string, options: object);
  constructor(private locale: string, private options?: object) {}

  format(value: string): string;
  format(value: number): string;
  format(value: string | number): string {
    return String(value);
  }
}
