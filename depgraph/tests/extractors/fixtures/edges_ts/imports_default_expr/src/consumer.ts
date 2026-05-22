// File B — default-imports the value from factory.
import thing from "./factory.js";

export function use() {
  return thing.name;
}
