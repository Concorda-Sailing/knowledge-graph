/**
 * TEMPLATE: copy to detectors/<your_name>.ts and fill in.
 *
 * A detector recognizes a specific framework or pattern in TS/JS
 * source. It receives the ts.SourceFile plus the primitives already
 * emitted for that file, and returns mutations.
 */
import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
  RelabelNode, AddEdge, AddNode,
} from "../detector_api.js";

export class MyDetector implements Detector {
  name = "my_detector"; // TODO: rename; matches filename without .ts

  detect(
    sourceFile: ts.SourceFile,
    primitives: Primitive[],
    ctx: DetectorContext,
  ): Mutation[] {
    const mutations: Mutation[] = [];

    // TODO: walk sourceFile looking for the construct you care about.
    // TODO: for each match, find the primitive in `primitives` by id
    //       and emit a RelabelNode.

    // Example:
    // const visit = (node: ts.Node) => {
    //   if (ts.isFunctionDeclaration(node) && isMyPattern(node)) {
    //     const id = `${ctx.repoKey}:${ctx.filePath}:${node.name?.text}`;
    //     mutations.push({
    //       type: "relabel", nodeId: id, newKind: "my_kind",
    //       metadata: { extra: "info" },
    //     });
    //   }
    //   ts.forEachChild(node, visit);
    // };
    // visit(sourceFile);

    return mutations;
  }
}
