import { hello } from "./a.js";

export function greet(name: string): string {
  return `hello ${name}`;
}

export function callBack(): string {
  return hello();
}
