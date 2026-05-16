import { expect } from "vitest";
import { add, normalize } from "./math.js";
import { makeFixture } from "./test_helpers.js";

export function testAdds() {
  const x = makeFixture();              // helper call — NOT a subject
  expect(add(1, 2)).toBe(3);            // subject: add
  expect(normalize("X")).toBe("x");     // subject: normalize
}
