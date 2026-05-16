export function topLevel(x: number): string { return String(x); }
export async function asyncFn() { return 1; }
export const arrow = (a: string) => a.length;
export const arrowConst: () => void = () => {};

export default function() { return 1; }   // anonymous default

export class Holder {
  method(x: number): string { return String(x); }
  async asyncMethod() {}
  static staticMethod() {}
  private privateMethod() {}

  // TS overloads: two declarations + one implementation. Only the
  // implementation should emit a primitive.
  format(x: number): string;
  format(x: string): string;
  format(x: any): string { return String(x); }

  // Same-name static + instance: must NOT collide on id.
  shared() { return "instance"; }
  static shared() { return "static"; }
}
