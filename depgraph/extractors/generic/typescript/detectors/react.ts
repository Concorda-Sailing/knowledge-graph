import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";

function returnsJsx(fn: ts.FunctionLikeDeclaration): boolean {
  let found = false;
  function walk(node: ts.Node) {
    if (found) return;
    if (
      ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node) ||
      ts.isJsxFragment(node)
    ) {
      found = true;
      return;
    }
    ts.forEachChild(node, walk);
  }
  if (fn.body) walk(fn.body);
  return found;
}

function pascal(name: string): boolean {
  return /^[A-Z]/.test(name);
}

function variableStatementComponents(
  node: ts.VariableStatement,
  ctx: DetectorContext,
  sf: ts.SourceFile,
): Mutation[] {
  const out: Mutation[] = [];
  for (const decl of node.declarationList.declarations) {
    if (!ts.isIdentifier(decl.name)) continue;
    const name = decl.name.text;
    if (!pascal(name)) continue;
    const init = decl.initializer;
    if (!init) continue;

    let via: string | null = null;
    let jsxOk = true;

    if (ts.isCallExpression(init)) {
      const callee = init.expression;
      const last = callee.getText(sf).split(".").pop() || "";
      if (last === "forwardRef" || last === "memo") {
        via = last;
        const arg = init.arguments[0];
        if (
          arg &&
          (ts.isArrowFunction(arg) || ts.isFunctionExpression(arg))
        ) {
          jsxOk = returnsJsx(arg as ts.ArrowFunction | ts.FunctionExpression);
        }
      }
    } else if (ts.isPropertyAccessExpression(init)) {
      via = "alias";
    }

    if (via && jsxOk) {
      const id = `${ctx.repoKey}:${ctx.filePath}:${name}`;
      const line = sf.getLineAndCharacterOfPosition(decl.getStart()).line + 1;
      const payload: Record<string, unknown> = {
        id, name, file: ctx.filePath, line, via,
      };
      if (via === "alias") {
        payload.aliases = init.getText(sf);
      }
      out.push({ type: "node", kind: "component", payload });
    }
  }
  return out;
}

function callsHook(fn: ts.FunctionLikeDeclaration): boolean {
  let found = false;
  function walk(node: ts.Node) {
    if (found) return;
    if (ts.isCallExpression(node)) {
      const t = node.expression.getText();
      const last = t.split(".").pop() || "";
      if (/^use[A-Z0-9]/.test(last)) {
        found = true;
        return;
      }
    }
    ts.forEachChild(node, walk);
  }
  if (fn.body) walk(fn.body);
  return found;
}

export class ReactDetector implements Detector {
  name = "react";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    const muts: Mutation[] = [];
    const byQualname = new Map<string, Primitive>();
    for (const p of primitives) {
      if (p.kind === "function") {
        const qual = p.id.split(":").slice(2).join(":");
        byQualname.set(qual, p);
      }
    }

    const visit = (node: ts.Node) => {
      if (
        (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)) &&
        node.name && ts.isIdentifier(node.name)
      ) {
        const name = node.name.text;
        const prim = byQualname.get(name);
        if (prim) {
          if (/^[A-Z]/.test(name) && returnsJsx(node)) {
            muts.push({ type: "relabel", nodeId: prim.id, newKind: "component" });
          } else if (/^use[A-Z0-9]/.test(name) && callsHook(node)) {
            muts.push({ type: "relabel", nodeId: prim.id, newKind: "hook" });
          }
        }
      }
      if (ts.isVariableStatement(node)) {
        muts.push(...variableStatementComponents(node, ctx, sf));
      }
      ts.forEachChild(node, visit);
    };
    visit(sf);
    return muts;
  }
}
