#!/usr/bin/env tsx
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as ts from "typescript";
import { Project, Node, SourceFile as TsMorphSourceFile } from "ts-morph";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "./detector_api.js";
import {
  slugifyIdTs, sha, canonicalIdForRepoSymbol,
} from "./canonical.js";
import {
  Edge, buildImportMap, buildInstanceMap, dedupeEdges,
  parseHttpCall, parseHttpCallTest,
} from "./detectors/_shared.js";

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
  component: "components", hook: "hooks", service: "services",
  test: "tests", route_call: "route_calls",
};

const MAX_STEM = 200;

function safeFilename(id: string): string {
  // Canonical TS ids use `::` as the separator; route them through slugifyIdTs
  // so the on-disk filename matches pre-flip.
  let stem: string;
  if (id.includes("::")) {
    stem = slugifyIdTs(id);
  } else {
    stem = id.replace(/\//g, "__").replace(/:/g, "__");
  }
  if (stem.length > MAX_STEM) {
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

// --------------------------------------------------------------------------- #
// Canonicalize stage: convert detector candidates into pre-flip-shape nodes.
// Mirrors the layout of extract_web.ts / extract_tests.ts. Uses the ts-morph
// Project (opened once per run) for module resolution + JSX/call walking.
// --------------------------------------------------------------------------- #

const PRIMITIVE_KINDS_TO_DROP = new Set([
  "module", "class", "function", "import_edge", "call_edge",
]);
const CANONICAL_REPO_SYMBOL_KINDS = new Set(["component", "hook", "service", "test"]);

interface CandidateNode {
  fullName: string;
  kind: "component" | "hook" | "service" | "test";
  file: string;
  symbolPos: number;
  symbolEnd: number;
  scopePos: number;
  scopeEnd: number;
  title?: string;
}

function isWebExtractor(repoKey: string): boolean {
  // Stamp matches pre-flip: web-style repos use extract_web.ts; the test repo
  // (concorda-test) uses extract_tests.ts. We detect by repo-key suffix to
  // stay stable across renames.
  return !repoKey.endsWith("-test");
}

function extractorStamp(repoKey: string): "extract_web.ts" | "extract_tests.ts" {
  return isWebExtractor(repoKey) ? "extract_web.ts" : "extract_tests.ts";
}

function dossierDir(kind: string): string {
  if (kind === "hook") return "hooks";
  if (kind === "component") return "components";
  if (kind === "service") return "services";
  if (kind === "test") return "tests";
  return kind + "s";
}

/** Find the ts-morph Node at exactly [pos, end] under sf. Symbol/scope nodes
 *  emitted by detectors carry their own ranges so canonicalize can locate
 *  them without re-running buildEmissions. */
function findNodeByRange(sf: TsMorphSourceFile, pos: number, end: number): Node | null {
  let hit: Node | null = null;
  sf.forEachDescendant((n) => {
    if (n.getStart() === pos && n.getEnd() === end && !hit) {
      hit = n;
    }
  });
  return hit;
}

/** Attribute edges from a scope node — JSX render edges, hook_call edges,
 *  http_call edges — onto the owning candidate. Ports extract_web.ts:
 *  attributeEdges, but the "owning emission" is fixed (we know which scope
 *  this walk is for) so we don't need scopeSet lookup. */
function attributeEdgesForScope(
  scope: Node,
  sf: TsMorphSourceFile,
  importMap: Map<string, string>,
  instanceMap: Map<string, string> | null,
  isTestRepo: boolean,
  edges: Edge[],
): void {
  const baseName = path.basename(sf.getFilePath());
  scope.forEachDescendant((node) => {
    // JSX render edges (web only — extract_tests.ts skipped these).
    if (!isTestRepo && (Node.isJsxOpeningElement(node) || Node.isJsxSelfClosingElement(node))) {
      const tag = node.getTagNameNode();
      let target: string | undefined;
      if (Node.isIdentifier(tag)) {
        const name = tag.getText();
        if (!/^[A-Z]/.test(name)) return;
        target = importMap.get(name);
      } else if (Node.isPropertyAccessExpression(tag)) {
        const leftName = tag.getExpression().getText();
        const importedLeft = importMap.get(leftName);
        if (importedLeft) target = `${importedLeft}.${tag.getName()}`;
      }
      if (!target) return;
      edges.push({
        target,
        via: "render",
        where: `${baseName}:${node.getStartLineNumber()}`,
        confidence: "exact",
      });
      return;
    }

    if (!Node.isCallExpression(node)) return;

    // HTTP edge?
    const httpEdge = isTestRepo ? parseHttpCallTest(node) : parseHttpCall(node);
    if (httpEdge) {
      edges.push(httpEdge);
      return;
    }

    // hook_call edge.
    const expr = node.getExpression();
    if (Node.isIdentifier(expr)) {
      const target = importMap.get(expr.getText());
      if (target) {
        edges.push({
          target,
          via: "hook_call",
          where: `${baseName}:${node.getStartLineNumber()}`,
          confidence: "exact",
        });
      }
    } else if (Node.isPropertyAccessExpression(expr)) {
      const left = expr.getExpression().getText();
      const right = expr.getName();
      const resolvedLeft = (instanceMap?.get(left)) ?? importMap.get(left);
      if (resolvedLeft) {
        edges.push({
          target: `${resolvedLeft}.${right}`,
          via: "hook_call",
          where: `${baseName}:${node.getStartLineNumber()}`,
          confidence: "exact",
        });
      }
    }
  });
}

function buildCanonicalRepoSymbolNode(
  c: CandidateNode,
  symbolNode: Node,
  scopeNode: Node,
  sf: TsMorphSourceFile,
  importMap: Map<string, string>,
  instanceMap: Map<string, string> | null,
  repoKey: string,
  isTestRepo: boolean,
): Primitive {
  const id = canonicalIdForRepoSymbol(repoKey, c.file, c.fullName);
  // Hash payload: insertion order {name, kind, text} — must match pre-flip.
  const hashPayload = {
    name: c.fullName,
    kind: c.kind,
    text: symbolNode.getText().slice(0, 1024),
  };
  const edges: Edge[] = [];
  // route_call kind never reaches here. For tests we don't attribute (pre-flip
  // extract_tests.ts does attribute hook_call/http_call onto class methods and
  // exported helpers — but emits an empty list for the test calls themselves
  // because findOwningEmission walks parents and the test() scope is the arrow
  // fn argument). Re-implement faithfully:
  attributeEdgesForScope(scopeNode, sf, importMap, instanceMap, isTestRepo, edges);
  const deduped = dedupeEdges(edges);
  const line = symbolNode.getStartLineNumber();
  const title = c.title ?? c.fullName;

  // signature: insertion order {name, kind}
  const signature = { name: c.fullName, kind: c.kind };

  // source: insertion order {repo, path, symbol, line}
  const source = {
    repo: repoKey,
    path: c.file,
    symbol: c.fullName,
    line,
  };

  return {
    id,
    kind: c.kind,
    schema_version: 1,
    title,
    feature: null,
    source,
    signature,
    structural_hash: sha(hashPayload),
    depends_on: deduped,
    external_consumers: [],
    tests: [],
    dossier: `dossiers/${dossierDir(c.kind)}/${slugifyIdTs(id)}.md`,
    extractor: extractorStamp(repoKey),
    warnings: [],
  };
}

/** Top-level canonicalize stage. Takes the detector-mutated primitive set
 *  and produces canonical nodes. The ts-morph Project is opened lazily —
 *  only if there are candidates that need it. */
function canonicalize(
  primitives: Primitive[],
  repoKey: string,
  repoPath: string,
  tsMorphSourceByFile: Map<string, TsMorphSourceFile>,
): Primitive[] {
  const out: Primitive[] = [];
  const isTestRepo = !isWebExtractor(repoKey);

  // Cache import/instance maps per file so multiple emissions in the same file
  // share the work.
  const importMaps = new Map<string, Map<string, string>>();
  const instanceMaps = new Map<string, Map<string, string>>();

  // Pass A: route_call nodes — already canonical, no resolution needed.
  for (const n of primitives) {
    if (n.kind === "route_call") {
      // The route-calls detector emits the full canonical payload directly.
      out.push({ ...n });
      continue;
    }
  }

  // Pass B: component / hook / service / test — need ts-morph attribution.
  for (const n of primitives) {
    if (PRIMITIVE_KINDS_TO_DROP.has(n.kind)) continue;
    if (n.kind === "route_call") continue;
    if (!CANONICAL_REPO_SYMBOL_KINDS.has(n.kind)) continue;

    // Detector-emitted AddNode payloads carry their _-prefixed metadata.
    const file = n._file as string | undefined;
    const fullName = n._full_name as string | undefined;
    const symbolPos = n._symbol_pos as number | undefined;
    const symbolEnd = n._symbol_end as number | undefined;
    const scopePos = n._scope_pos as number | undefined;
    const scopeEnd = n._scope_end as number | undefined;
    const title = n._title as string | undefined;

    if (file === undefined || fullName === undefined ||
        symbolPos === undefined || symbolEnd === undefined ||
        scopePos === undefined || scopeEnd === undefined) {
      // Not a TS-detector candidate (relabel primitives etc.) — skip.
      continue;
    }

    const sf = tsMorphSourceByFile.get(file);
    if (!sf) continue;

    const symbolNode = findNodeByRange(sf, symbolPos, symbolEnd);
    const scopeNode = findNodeByRange(sf, scopePos, scopeEnd);
    if (!symbolNode || !scopeNode) continue;

    let importMap = importMaps.get(file);
    if (!importMap) {
      importMap = buildImportMap(sf, repoKey, repoPath);
      importMaps.set(file, importMap);
    }
    let instanceMap: Map<string, string> | null = null;
    if (isTestRepo) {
      let im = instanceMaps.get(file);
      if (!im) {
        im = buildInstanceMap(sf, importMap);
        instanceMaps.set(file, im);
      }
      instanceMap = im;
    }

    const c: CandidateNode = {
      fullName,
      kind: n.kind as CandidateNode["kind"],
      file,
      symbolPos, symbolEnd, scopePos, scopeEnd,
      title,
    };
    out.push(buildCanonicalRepoSymbolNode(
      c, symbolNode, scopeNode, sf, importMap, instanceMap, repoKey, isTestRepo,
    ));
  }

  return out;
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

  // Open a single ts-morph Project for module resolution. Falls back to no
  // tsconfig if one isn't present (e.g. plain JS repos), in which case import
  // resolution returns null and we emit no module-internal edges.
  const tsconfigPath = path.join(repoPath, "tsconfig.json");
  const project = new Project({
    tsConfigFilePath: fs.existsSync(tsconfigPath) ? tsconfigPath : undefined,
    skipAddingFilesFromTsConfig: !fs.existsSync(tsconfigPath),
  });
  if (!fs.existsSync(tsconfigPath)) {
    // No tsconfig — add the files we'll process so getModuleSpecifierSourceFile
    // can still resolve relative imports.
    for (const f of (only ? [only] : Array.from(discoverFiles(repoPath, excludes)))) {
      project.addSourceFileAtPathIfExists(f);
    }
  }

  const files = only ? [only] : Array.from(discoverFiles(repoPath, excludes));
  const tsMorphSourceByFile = new Map<string, TsMorphSourceFile>();
  let total = 0, relabels = 0, detectorNodes = 0, detectorEdges = 0, skipped = 0;
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

    // Pull (or load) the ts-morph SourceFile for the same path. ts-morph uses
    // the same path semantics as the discover walk.
    let tsf = project.getSourceFile(f);
    if (!tsf) tsf = project.addSourceFileAtPathIfExists(f) || undefined;
    if (tsf) tsMorphSourceByFile.set(rel, tsf);

    const ctx: DetectorContext = {
      repoKey, filePath: rel, projectConfig: { detectors: names },
      repoPath, tsMorphSf: tsf,
    };
    const muts: Mutation[] = [];
    for (const d of detectors) {
      try { muts.push(...d.detect(sf, prims, ctx)); }
      catch (e) { console.error(`detector_error: ${d.name} on ${rel}: ${e}`); }
    }
    // Break detector output down by mutation type. The previous metric
    // only counted "relabel" mutations, but the current detector set
    // (react, route-calls, service, vitest) emits "node" mutations to
    // add components/hooks/route_calls/tests on top of the AST primitives,
    // so the metric always read 0 and the regen summary was misleading.
    for (const m of muts) {
      if (m.type === "relabel") relabels++;
      else if (m.type === "node") detectorNodes++;
      else if (m.type === "edge") detectorEdges++;
    }
    const nodes = applyMutations(prims, muts);
    allNodes.push(...nodes);
    total += nodes.length;
  }

  const canonical = canonicalize(allNodes, repoKey, repoPath, tsMorphSourceByFile);
  writeNodes(canonical, dataDir);
  console.log(
    `wrote ${canonical.length} canonical nodes ` +
    `(${total} primitives; from detectors: ${relabels} relabels, ${detectorNodes} nodes, ${detectorEdges} edges), ` +
    `skipped ${skipped} files`,
  );
}

main().catch(e => { console.error(e); process.exit(1); });
