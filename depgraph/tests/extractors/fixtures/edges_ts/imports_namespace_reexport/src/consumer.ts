// Consumer — imports the namespace-bound name from the barrel.
import { helpers } from "./barrel.js";

export function use() {
  return helpers.snake("FooBar");
}
