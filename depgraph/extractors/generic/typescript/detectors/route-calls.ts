import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";

function extractUrl(node: ts.CallExpression): string | null {
  if (!ts.isIdentifier(node.expression) || node.expression.text !== "fetch") return null;
  const arg = node.arguments[0];
  if (arg && ts.isStringLiteralLike(arg)) return arg.text;
  if (arg && ts.isTemplateExpression(arg)) {
    // Preserve template literal head as best-effort target.
    return arg.head.text + "{...}";
  }
  return null;
}

export class RouteCallsDetector implements Detector {
  name = "route-calls";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    const muts: Mutation[] = [];
    let currentFnId: string | null = null;
    const byQualname = new Map<string, Primitive>();
    for (const p of primitives) {
      if (p.kind === "function") {
        byQualname.set(p.id.split(":").slice(2).join(":"), p);
      }
    }

    const visit = (node: ts.Node) => {
      let prevFn = currentFnId;
      if ((ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node))
          && node.name && ts.isIdentifier(node.name)) {
        const prim = byQualname.get(node.name.text);
        if (prim) currentFnId = prim.id;
      }
      if (ts.isCallExpression(node)) {
        const url = extractUrl(node);
        if (url) {
          const line = sf.getLineAndCharacterOfPosition(node.getStart()).line + 1;
          muts.push({
            type: "node", kind: "route_call",
            payload: {
              id: `${ctx.repoKey}:${ctx.filePath}:rc:${line}`,
              url, file: ctx.filePath, line,
              from_id: currentFnId,
            },
          });
        }
      }
      ts.forEachChild(node, visit);
      currentFnId = prevFn;
    };
    visit(sf);
    return muts;
  }
}
