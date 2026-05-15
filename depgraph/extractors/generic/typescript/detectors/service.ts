/**
 * Detect service-layer functions.
 *
 * A TS function is labeled kind=service if it lives under a directory
 * named lib, pages, services, or utils (at any depth) and is:
 *   - module-level (no enclosing class),
 *   - public (does not start with `_`),
 *   - either a function declaration OR a const-arrow function declared
 *     at the top of the file.
 *
 * Path convention only — no framework recognition. Lifted from
 * Concorda's TS extractor.
 */
import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";

const SERVICE_DIRS = new Set(["lib", "pages", "services", "utils"]);

function isServicePath(filePath: string): boolean {
  return filePath.split("/").some((p) => SERVICE_DIRS.has(p));
}

export class ServiceDetector implements Detector {
  name = "service";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    if (!isServicePath(ctx.filePath)) return [];
    const muts: Mutation[] = [];
    for (const p of primitives) {
      if (p.kind !== "function") continue;
      if (p.parentId != null) continue;  // method, skip
      if (typeof p.name === "string" && p.name.startsWith("_")) continue;
      muts.push({ type: "relabel", nodeId: p.id, newKind: "service" });
    }
    return muts;
  }
}
