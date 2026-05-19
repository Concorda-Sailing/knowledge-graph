// External namespace import (npm) — fs is not in node_modules under the
// fixture so it resolves to `external::npm::fs`.
import * as fs from "fs";
// External named import — readFile is a named external symbol.
import { readFile } from "fs/promises";
// In-corpus namespace import — util resolves to a corpus module.
import * as util from "./local/util.js";
// Plain unresolved bare receiver — no var-type, no import.
declare const mystery: any;

export function root() {
  // R7 regression #69: previously this dropped silently. Now we expect an
  // edge to `external::npm::fs::readFile` with confidence "exact".
  fs.readFile("p", () => {});

  // Method on an in-corpus namespace import resolves to the exporting file.
  util.greet();

  // Bare receiver with no binding info — should still emit
  // `external::unresolved::mystery.doSomething`, never silently drop.
  mystery.doSomething();
}
