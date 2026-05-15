import * as ts from "typescript";

export type RelabelNode = {
  type: "relabel";
  nodeId: string;
  newKind: string;
  metadata?: Record<string, unknown>;
};

export type AddEdge = {
  type: "edge";
  fromId: string;
  toId: string;
  kind: string;
};

export type AddNode = {
  type: "node";
  kind: string;
  payload: Record<string, unknown>;
};

export type Mutation = RelabelNode | AddEdge | AddNode;

export type DetectorContext = {
  repoKey: string;
  filePath: string;
  projectConfig: Record<string, unknown>;
};

export type Primitive = {
  id: string;
  kind: string;
  name?: string;
  file?: string;
  parentId?: string | null;
  [k: string]: unknown;
};

export interface Detector {
  name: string;
  detect(
    sourceFile: ts.SourceFile,
    primitives: Primitive[],
    ctx: DetectorContext,
  ): Mutation[];
}
