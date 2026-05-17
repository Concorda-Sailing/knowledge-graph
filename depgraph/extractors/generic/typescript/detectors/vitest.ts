/** Vitest/Playwright detector — emits test/service AddNode mutations with
 *  metadata canonicalize() reads to build canonical nodes.
 *
 *  Despite the file name, this detector also handles Playwright `.spec.ts`
 *  files; the two test runners share enough surface to use one pipeline. */

import * as ts from "typescript";
import { Node } from "ts-morph";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";

const TEST_VERBS = new Set(["only", "skip", "fixme"]);

function isSpecFile(fp: string): boolean {
  return fp.endsWith(".spec.ts") || fp.endsWith(".spec.tsx");
}

interface Candidate {
  fullName: string;
  kind: "test" | "service" | "component";
  symbolPos: number;
  symbolEnd: number;
  scopePos: number;
  scopeEnd: number;
  title?: string;
}

function emit(c: Candidate, ctx: DetectorContext): Mutation {
  const payload: Record<string, unknown> = {
    id: `${ctx.repoKey}::${ctx.filePath}::${c.fullName}`,
    _full_name: c.fullName,
    _file: ctx.filePath,
    _symbol_pos: c.symbolPos,
    _symbol_end: c.symbolEnd,
    _scope_pos: c.scopePos,
    _scope_end: c.scopeEnd,
  };
  if (c.title !== undefined) payload._title = c.title;
  return { type: "node", kind: c.kind, payload };
}

export class VitestDetector implements Detector {
  name = "vitest";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    if (!ctx.tsMorphSf) return [];
    const tsf = ctx.tsMorphSf;
    const muts: Mutation[] = [];

    // 1. Exported top-level functions + arrow consts + object-literal methods.
    for (const decl of tsf.getFunctions()) {
      const name = decl.getName();
      if (!name) continue;
      muts.push(emit({
        fullName: name,
        kind: "service",
        symbolPos: decl.getStart(),
        symbolEnd: decl.getEnd(),
        scopePos: decl.getStart(),
        scopeEnd: decl.getEnd(),
      }, ctx));
    }

    for (const stmt of tsf.getVariableStatements()) {
      if (!stmt.isExported()) continue;
      for (const varDecl of stmt.getDeclarations()) {
        const name = varDecl.getName();
        const init = varDecl.getInitializer();
        if (!name || !init) continue;
        if (Node.isArrowFunction(init) || Node.isFunctionExpression(init)) {
          muts.push(emit({
            fullName: name,
            kind: "service",
            symbolPos: varDecl.getStart(),
            symbolEnd: varDecl.getEnd(),
            scopePos: init.getStart(),
            scopeEnd: init.getEnd(),
          }, ctx));
        } else if (Node.isObjectLiteralExpression(init)) {
          for (const prop of init.getProperties()) {
            if (Node.isPropertyAssignment(prop)) {
              const propInit = prop.getInitializer();
              if (propInit && (Node.isArrowFunction(propInit) || Node.isFunctionExpression(propInit))) {
                muts.push(emit({
                  fullName: `${name}.${prop.getName()}`,
                  kind: "service",
                  symbolPos: prop.getStart(),
                  symbolEnd: prop.getEnd(),
                  scopePos: propInit.getStart(),
                  scopeEnd: propInit.getEnd(),
                }, ctx));
              }
            }
          }
        }
      }
    }

    // 2. Class methods (skip private).
    for (const cls of tsf.getClasses()) {
      const className = cls.getName();
      if (!className) continue;
      for (const m of cls.getMethods()) {
        const methodName = m.getName();
        if (!methodName) continue;
        if (m.getModifiers().some((mod) => mod.getText() === "private")) continue;
        muts.push(emit({
          fullName: `${className}.${methodName}`,
          kind: "service",
          symbolPos: m.getStart(),
          symbolEnd: m.getEnd(),
          scopePos: m.getStart(),
          scopeEnd: m.getEnd(),
        }, ctx));
      }
    }

    // 3. test(...) / test.only / test.skip / test.fixme in .spec files.
    if (isSpecFile(tsf.getFilePath())) {
      tsf.forEachDescendant((node) => {
        if (!Node.isCallExpression(node)) return;
        const expr = node.getExpression();
        let isTest = false;
        if (Node.isIdentifier(expr) && expr.getText() === "test") {
          isTest = true;
        } else if (Node.isPropertyAccessExpression(expr)) {
          const left = expr.getExpression().getText();
          const right = expr.getName();
          if (left === "test" && TEST_VERBS.has(right)) isTest = true;
        }
        if (!isTest) return;

        const args = node.getArguments();
        if (args.length < 2) return;
        const nameArg = args[0];
        let title = "(unnamed)";
        if (Node.isStringLiteral(nameArg)) title = nameArg.getLiteralText();
        else if (Node.isNoSubstitutionTemplateLiteral(nameArg)) title = nameArg.getLiteralText();

        const fnArg = args[args.length - 1];
        if (!Node.isArrowFunction(fnArg) && !Node.isFunctionExpression(fnArg)) return;

        const line = node.getStartLineNumber();
        const fullName = `test@${line}`;
        muts.push(emit({
          fullName,
          kind: "test",
          symbolPos: node.getStart(),
          symbolEnd: node.getEnd(),
          scopePos: fnArg.getStart(),
          scopeEnd: fnArg.getEnd(),
          title,
        }, ctx));
      });
    }

    return muts;
  }
}
