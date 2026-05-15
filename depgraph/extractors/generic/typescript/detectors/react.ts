/** React detector — ports buildEmissions() from pre-flip extract_web.ts.
 *
 *  Emits AddNode mutations carrying all metadata needed by canonicalize():
 *    - fullName     : the symbol name (e.g. "Foo" or "apiClient.get")
 *    - kind         : "component" | "hook" | "service" (decided here)
 *    - line         : symbol node start line
 *    - text         : first 1024 chars of symbolNode.getText() for the hash
 *    - scopePos     : start position of the *scope* node used for edge
 *                     attribution (a child of symbolNode, e.g. inner arrow
 *                     for HOC-wrapped components).
 *    - scopeEnd     : end position of the scope node.
 *  canonicalize() in extract.ts uses scopePos/scopeEnd to find the same
 *  ts-morph Node and walk its descendants for depends_on attribution. */

import * as ts from "typescript";
import { Node, SyntaxKind } from "ts-morph";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";

const HOC_NAMES = new Set(["forwardRef", "memo"]);

function classify(name: string): "component" | "hook" | "service" {
  if (/^use[A-Z]/.test(name)) return "hook";
  if (/^[A-Z]/.test(name)) return "component";
  return "service";
}

interface Candidate {
  fullName: string;
  kind: "component" | "hook" | "service";
  symbolPos: number;
  symbolEnd: number;
  scopePos: number;
  scopeEnd: number;
}

function emit(c: Candidate, ctx: DetectorContext): Mutation {
  return {
    type: "node",
    kind: c.kind,
    payload: {
      id: `${ctx.repoKey}::${ctx.filePath}::${c.fullName}`,
      _full_name: c.fullName,
      _file: ctx.filePath,
      _symbol_pos: c.symbolPos,
      _symbol_end: c.symbolEnd,
      _scope_pos: c.scopePos,
      _scope_end: c.scopeEnd,
    },
  };
}

export class ReactDetector implements Detector {
  name = "react";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    if (!ctx.tsMorphSf) return [];
    const tsf = ctx.tsMorphSf;
    const muts: Mutation[] = [];

    // Collect re-exported names: `export { Button }` after `const Button = ...`.
    const reExportedNames = new Set<string>();
    for (const exp of tsf.getExportDeclarations()) {
      for (const spec of exp.getNamedExports()) {
        reExportedNames.add(spec.getNameNode().getText());
      }
    }

    // 1. Function declarations.
    for (const decl of tsf.getFunctions()) {
      const name = decl.getName();
      if (!name) continue;
      muts.push(emit({
        fullName: name,
        kind: classify(name),
        symbolPos: decl.getStart(),
        symbolEnd: decl.getEnd(),
        scopePos: decl.getStart(),
        scopeEnd: decl.getEnd(),
      }, ctx));
    }

    // 2. Variable statements.
    for (const stmt of tsf.getVariableStatements()) {
      const directlyExported = stmt.isExported();
      for (const varDecl of stmt.getDeclarations()) {
        const name = varDecl.getName();
        const init = varDecl.getInitializer();
        if (!name || !init) continue;
        if (!directlyExported && !reExportedNames.has(name)) continue;

        if (Node.isArrowFunction(init) || Node.isFunctionExpression(init)) {
          muts.push(emit({
            fullName: name,
            kind: classify(name),
            symbolPos: varDecl.getStart(),
            symbolEnd: varDecl.getEnd(),
            scopePos: init.getStart(),
            scopeEnd: init.getEnd(),
          }, ctx));
          continue;
        }

        // HOC-wrapped components: forwardRef / memo with arrow as arg[0].
        if (Node.isCallExpression(init)) {
          const expr = init.getExpression();
          let calleeName = "";
          if (Node.isIdentifier(expr)) calleeName = expr.getText();
          else if (Node.isPropertyAccessExpression(expr)) calleeName = expr.getName();
          if (HOC_NAMES.has(calleeName)) {
            const args = init.getArguments();
            if (args.length > 0) {
              const arg0 = args[0];
              if (Node.isArrowFunction(arg0) || Node.isFunctionExpression(arg0)) {
                muts.push(emit({
                  fullName: name,
                  kind: classify(name),
                  symbolPos: varDecl.getStart(),
                  symbolEnd: varDecl.getEnd(),
                  scopePos: arg0.getStart(),
                  scopeEnd: arg0.getEnd(),
                }, ctx));
                continue;
              }
            }
          }
        }

        // Pure alias: `const Dialog = DialogPrimitive.Root`.
        if (Node.isPropertyAccessExpression(init)) {
          muts.push(emit({
            fullName: name,
            kind: classify(name),
            symbolPos: varDecl.getStart(),
            symbolEnd: varDecl.getEnd(),
            scopePos: varDecl.getStart(),
            scopeEnd: varDecl.getEnd(),
          }, ctx));
          continue;
        }

        // Object literal: `export const profileApi = { get: () => ... }`.
        if (Node.isObjectLiteralExpression(init)) {
          for (const prop of init.getProperties()) {
            if (Node.isPropertyAssignment(prop)) {
              const propName = prop.getName();
              const propInit = prop.getInitializer();
              if (!propInit) continue;
              if (Node.isArrowFunction(propInit) || Node.isFunctionExpression(propInit)) {
                muts.push(emit({
                  fullName: `${name}.${propName}`,
                  kind: "service",
                  symbolPos: prop.getStart(),
                  symbolEnd: prop.getEnd(),
                  scopePos: propInit.getStart(),
                  scopeEnd: propInit.getEnd(),
                }, ctx));
              }
            } else if (Node.isMethodDeclaration(prop)) {
              const propName = prop.getName();
              muts.push(emit({
                fullName: `${name}.${propName}`,
                kind: "service",
                symbolPos: prop.getStart(),
                symbolEnd: prop.getEnd(),
                scopePos: prop.getStart(),
                scopeEnd: prop.getEnd(),
              }, ctx));
            }
          }
        }
      }
    }

    return muts;
  }
}
