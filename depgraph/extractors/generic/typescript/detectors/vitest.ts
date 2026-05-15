import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive, AddNode,
} from "../detector_api.js";

const TEST_FILE_RE = /(\.test|\.spec)\.(ts|tsx|js|jsx)$/;

export class VitestDetector implements Detector {
  name = "vitest";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    if (!TEST_FILE_RE.test(ctx.filePath)) return [];
    const muts: Mutation[] = [];
    const describeStack: string[] = [];

    const visit = (node: ts.Node) => {
      if (ts.isCallExpression(node) && ts.isIdentifier(node.expression)) {
        const fnName = node.expression.text;
        const firstArg = node.arguments[0];
        const label = firstArg && ts.isStringLiteralLike(firstArg) ? firstArg.text : "";
        if (fnName === "describe" && label) {
          describeStack.push(label);
          ts.forEachChild(node, visit);
          describeStack.pop();
          return;
        }
        if ((fnName === "it" || fnName === "test") && label) {
          const qual = [...describeStack, label].join(" > ");
          muts.push({
            type: "node",
            kind: "test",
            payload: {
              id: `${ctx.repoKey}:${ctx.filePath}:test:${qual}`,
              name: label,
              file: ctx.filePath,
              describe_path: [...describeStack],
              line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1,
            },
          });
        }
      }
      ts.forEachChild(node, visit);
    };
    visit(sf);
    return muts;
  }
}
