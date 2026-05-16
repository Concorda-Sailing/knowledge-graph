// Fixture: anonymous_zoo
// Tests: anonymous default exports, named function expressions, arrow vs function distinction.

// 1. Named arrow function assigned to const (function primitive via variable-decl name)
export const greet = (name: string): string => `Hello, ${name}`;

// 2. Named function expression assigned to const — name on expression differs from decl name
export const handler = function myHandler(x: number): number {
  return x * 2;
};

// 3. Anonymous arrow in a variable (no function keyword, no expression name)
export const transform = (xs: number[]): number[] => xs.map((n) => n + 1);

// 4. Default-exported anonymous arrow function
export default (input: string): boolean => input.length > 0;
