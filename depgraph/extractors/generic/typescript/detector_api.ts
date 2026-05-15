import * as ts from "typescript";
import type { SourceFile as TsMorphSourceFile } from "ts-morph";

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
  /** Absolute path of the repo root (so detectors can compute relative paths
   *  consistent with ts-morph's getFilePath() output). */
  repoPath?: string;
  /** ts-morph SourceFile for the same file as `sourceFile`. Present only when
   *  the extractor opened a ts-morph Project (the default for TypeScript
   *  detectors that need import resolution). */
  tsMorphSf?: TsMorphSourceFile;
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
