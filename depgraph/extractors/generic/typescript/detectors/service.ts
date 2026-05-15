/**
 * Service detector — emits service AddNode candidates for top-level
 * functions and arrow consts that live under lib/, pages/, services/, or
 * utils/ (at any depth). Skips private (`_`-prefixed) names.
 *
 * Emits the same _-prefixed canonical metadata as react.ts so the shared
 * canonicalize() stage in extract.ts can build the canonical service node.
 *
 * Path convention only — no framework recognition. Lifted from Concorda's TS
 * extractor.
 */
import * as ts from "typescript";
import { Node } from "ts-morph";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";

const SERVICE_DIRS = new Set(["lib", "pages", "services", "utils"]);

function isServicePath(filePath: string): boolean {
  return filePath.split("/").some((p) => SERVICE_DIRS.has(p));
}

function emit(
  fullName: string,
  symbolPos: number, symbolEnd: number,
  scopePos: number, scopeEnd: number,
  ctx: DetectorContext,
): Mutation {
  return {
    type: "node",
    kind: "service",
    payload: {
      id: `${ctx.repoKey}::${ctx.filePath}::${fullName}`,
      _full_name: fullName,
      _file: ctx.filePath,
      _symbol_pos: symbolPos,
      _symbol_end: symbolEnd,
      _scope_pos: scopePos,
      _scope_end: scopeEnd,
    },
  };
}

export class ServiceDetector implements Detector {
  name = "service";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    if (!isServicePath(ctx.filePath)) return [];
    if (!ctx.tsMorphSf) return [];
    const tsf = ctx.tsMorphSf;
    const muts: Mutation[] = [];

    for (const decl of tsf.getFunctions()) {
      const name = decl.getName();
      if (!name) continue;
      if (name.startsWith("_")) continue;
      muts.push(emit(
        name,
        decl.getStart(), decl.getEnd(),
        decl.getStart(), decl.getEnd(),
        ctx,
      ));
    }

    for (const stmt of tsf.getVariableStatements()) {
      if (!stmt.isExported()) continue;
      for (const varDecl of stmt.getDeclarations()) {
        const name = varDecl.getName();
        const init = varDecl.getInitializer();
        if (!name || !init) continue;
        if (name.startsWith("_")) continue;
        if (Node.isArrowFunction(init) || Node.isFunctionExpression(init)) {
          muts.push(emit(
            name,
            varDecl.getStart(), varDecl.getEnd(),
            init.getStart(), init.getEnd(),
            ctx,
          ));
        }
      }
    }
    return muts;
  }
}
