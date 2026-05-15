#!/usr/bin/env tsx
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as ts from "typescript";
import {
  Detector, DetectorContext, Mutation, Primitive,
  RelabelNode, AddEdge, AddNode,
} from "./detector_api.js";

const DEFAULT_EXCLUDES = new Set([
  "node_modules", "dist", "build", ".git", "coverage", ".next",
  ".turbo", "target", ".venv",
]);
const SOURCE_EXTS = new Set([".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"]);

function* discoverFiles(root: string, extraExcludes: string[]): Generator<string> {
  const excludes = new Set([...DEFAULT_EXCLUDES, ...extraExcludes]);
  function* walk(dir: string): Generator<string> {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      const rel = path.relative(root, full).split(path.sep);
      if (rel.some((p) => excludes.has(p))) continue;
      if (entry.isDirectory()) yield* walk(full);
      else if (entry.isFile() && SOURCE_EXTS.has(path.extname(entry.name))) {
        yield full;
      }
    }
  }
  yield* walk(root);
}

function emitPrimitives(
  sf: ts.SourceFile,
  repoKey: string,
  relPath: string,
): Primitive[] {
  const out: Primitive[] = [];
  const moduleId = `${repoKey}:${relPath}:<module>`;
  out.push({
    id: moduleId, kind: "module", repo: repoKey, file: relPath,
    name: "<module>", parentId: null,
  });

  const classStack: string[] = [];
  let currentFnId: string | null = null;

  const visit = (node: ts.Node) => {
    if (ts.isClassDeclaration(node) && node.name) {
      const qual = [...classStack, node.name.text].join(".");
      const id = `${repoKey}:${relPath}:${qual}`;
      out.push({
        id, kind: "class", repo: repoKey, file: relPath,
        name: node.name.text, parentId: moduleId,
        line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1,
      });
      classStack.push(node.name.text);
      ts.forEachChild(node, visit);
      classStack.pop();
      return;
    }
    if (
      (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node) ||
       ts.isArrowFunction(node) || ts.isFunctionExpression(node)) &&
      "name" in node && node.name && ts.isIdentifier(node.name)
    ) {
      const name = node.name.text;
      const qual = [...classStack, name].join(".");
      const id = `${repoKey}:${relPath}:${qual}`;
      out.push({
        id, kind: "function", repo: repoKey, file: relPath,
        name, parentId: classStack.length ? `${repoKey}:${relPath}:${classStack.join(".")}` : null,
        line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1,
        isExported: !!(node.modifiers || []).find(m => m.kind === ts.SyntaxKind.ExportKeyword),
      });
      const prevFn = currentFnId;
      currentFnId = id;
      ts.forEachChild(node, visit);
      currentFnId = prevFn;
      return;
    }
    if (ts.isImportDeclaration(node)) {
      const spec = node.moduleSpecifier;
      if (ts.isStringLiteral(spec)) {
        out.push({
          id: `${moduleId}#import:${spec.text}`,
          kind: "import_edge", from_id: moduleId,
          target: spec.text,
          line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1,
        });
      }
    }
    if (ts.isCallExpression(node)) {
      let target = node.expression.getText(sf);
      const line = sf.getLineAndCharacterOfPosition(node.getStart()).line + 1;
      const origin = currentFnId ?? moduleId;
      out.push({
        id: `${origin}#call:${target}:${line}`,
        kind: "call_edge", from_id: origin, target, line,
      });
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
  return out;
}

const KIND_DIR: Record<string, string> = {
  module: "modules", class: "classes", function: "functions",
  import_edge: "imports", call_edge: "calls",
};

const MAX_STEM = 200;

function safeFilename(id: string): string {
  let stem = id.replace(/\//g, "__").replace(/:/g, "__");
  if (stem.length > MAX_STEM) {
    // Use a simple djb2-style hash for the truncation suffix so the filename
    // is still deterministic and collision-resistant without needing crypto.
    let h = 5381;
    for (let i = 0; i < stem.length; i++) h = ((h * 33) ^ stem.charCodeAt(i)) >>> 0;
    stem = stem.slice(0, MAX_STEM) + "__" + h.toString(16).padStart(8, "0");
  }
  return stem + ".json";
}

function writeNodes(nodes: Primitive[], dataDir: string): void {
  for (const n of nodes) {
    const sub = KIND_DIR[n.kind as string] ?? `${n.kind}s`;
    const dir = path.join(dataDir, "nodes", sub);
    fs.mkdirSync(dir, { recursive: true });
    const sorted = Object.fromEntries(
      Object.entries(n).sort(([a],[b]) => a.localeCompare(b))
    );
    fs.writeFileSync(
      path.join(dir, safeFilename(n.id)),
      JSON.stringify(sorted, null, 2) + "\n",
    );
  }
}

function applyMutations(prims: Primitive[], muts: Mutation[]): Primitive[] {
  const byId = new Map(prims.map(p => [p.id, { ...p }]));
  const extras: Primitive[] = [];
  for (const m of muts) {
    if (m.type === "relabel") {
      const n = byId.get(m.nodeId);
      if (n) {
        n.kind = m.newKind;
        Object.assign(n, m.metadata ?? {});
      }
    } else if (m.type === "node") {
      extras.push({ id: m.payload.id as string, kind: m.kind, ...m.payload });
    } else if (m.type === "edge") {
      extras.push({
        id: `${m.fromId}#edge:${m.kind}:${m.toId}`,
        kind: `${m.kind}_edge`,
        from_id: m.fromId, to_id: m.toId,
      });
    }
  }
  return [...byId.values(), ...extras];
}

async function loadDetectors(names: string[], extraPaths: string[]): Promise<Detector[]> {
  if (names.length === 0) return [];
  const frameworkDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "detectors");
  const search = [frameworkDir, ...extraPaths];
  const out: Detector[] = [];
  for (const name of names) {
    let found: Detector | null = null;
    for (const dir of search) {
      const candidate = path.join(dir, `${name}.ts`);
      if (fs.existsSync(candidate)) {
        const mod = await import(pathToFileURL(candidate).href);
        const cls = Object.values(mod).find((v: any) =>
          typeof v === "function" && v.prototype && typeof v.prototype.detect === "function"
        ) as (new () => Detector) | undefined;
        if (cls) { found = new cls(); break; }
      }
    }
    if (!found) {
      throw new Error(`unknown detector: ${name}`);
    }
    out.push(found);
  }
  return out;
}

function parseArgs(argv: string[]) {
  const opts: Record<string, string | string[]> = {
    "--repo-key": "", "--repo-path": "", "--data-dir": "",
    "--detectors": "", "--detector-path": [], "--exclude": [], "--only": "",
  };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k in opts) {
      const v = argv[++i];
      if (Array.isArray(opts[k])) (opts[k] as string[]).push(v);
      else opts[k] = v;
    }
  }
  return opts;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const repoKey = args["--repo-key"] as string;
  const repoPath = args["--repo-path"] as string;
  const dataDir = args["--data-dir"] as string;
  const names = (args["--detectors"] as string).split(",").map(s => s.trim()).filter(Boolean);
  const detectors = await loadDetectors(names, args["--detector-path"] as string[]);
  const excludes = args["--exclude"] as string[];
  const only = args["--only"] as string;

  const files = only ? [only] : Array.from(discoverFiles(repoPath, excludes));
  let total = 0, labeled = 0, skipped = 0;
  const allNodes: Primitive[] = [];

  for (const f of files) {
    let source: string;
    try { source = fs.readFileSync(f, "utf-8"); }
    catch (e) { console.error(`parse_error: ${f}: ${e}`); skipped++; continue; }
    let sf: ts.SourceFile;
    try {
      sf = ts.createSourceFile(f, source, ts.ScriptTarget.Latest, true,
        f.endsWith(".tsx") || f.endsWith(".jsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
    } catch (e) { console.error(`parse_error: ${f}: ${e}`); skipped++; continue; }

    const rel = path.relative(repoPath, f).split(path.sep).join("/");
    const prims = emitPrimitives(sf, repoKey, rel);
    const ctx: DetectorContext = {
      repoKey, filePath: rel, projectConfig: { detectors: names },
    };
    const muts: Mutation[] = [];
    for (const d of detectors) {
      try { muts.push(...d.detect(sf, prims, ctx)); }
      catch (e) { console.error(`detector_error: ${d.name} on ${rel}: ${e}`); }
    }
    labeled += muts.filter(m => m.type === "relabel").length;
    const nodes = applyMutations(prims, muts);
    allNodes.push(...nodes);
    total += nodes.length;
  }

  writeNodes(allNodes, dataDir);
  console.log(`wrote ${total} nodes (${labeled} labeled by detectors), skipped ${skipped} files`);
}

main().catch(e => { console.error(e); process.exit(1); });
