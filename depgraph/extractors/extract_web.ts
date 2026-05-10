#!/usr/bin/env -S npx tsx
/**
 * extract_web.ts — walk concorda-web source and emit:
 *   - component nodes (PascalCase function decls, arrow consts, default-exported components)
 *   - hook nodes (`use*` decls or arrow consts)
 *   - service nodes (methods inside an exported object literal — e.g. inviteApi.acceptInvite)
 *
 * For each node we record:
 *   - http_call edges: every fetchApi / fetchApiAuthenticated / fetch / apiClient.<verb>
 *     call site whose URL canonicalizes to /api/... (cross-HTTP-boundary edges)
 *   - hook_call edges: every CallExpression whose callee is a top-level imported
 *     identifier (or `imported.method`); used by reconciler for transitive dependents
 *
 * Each call expression is attributed to its nearest enclosing emitted node by
 * climbing the AST. This handles handler arrow functions inside React components
 * and arrow methods inside object literals (the api.ts pattern).
 */

import { Project, Node, SyntaxKind, SourceFile, CallExpression } from "ts-morph";
import * as crypto from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";

const REPO = process.env.CONCORDA_WEB_PATH ?? path.join(process.env.HOME!, "concorda-web");
const REPO_NAME = process.env.CONCORDA_WEB_REPO_NAME ?? "concorda-web";
const DEPGRAPH = process.env.CONCORDA_DEPGRAPH_PATH ?? path.join(process.env.HOME!, "concorda", "depgraph");
const NODES_DIR = path.join(DEPGRAPH, "nodes");

type EdgeVia = "import" | "http_call" | "render" | "hook_call" | "string_url";
type EdgeConfidence = "exact" | "fuzzy" | "inferred";

interface Edge {
  target: string;
  via: EdgeVia;
  where: string;
  confidence: EdgeConfidence;
}

interface NodeJson {
  schema_version: 1;
  id: string;
  kind: "component" | "hook" | "service";
  title: string;
  feature: string | null;
  source: { repo: string; path: string; symbol: string; line: number };
  signature: Record<string, unknown>;
  structural_hash: string;
  depends_on: Edge[];
  external_consumers: unknown[];
  tests: string[];
  dossier: string;
  extractor: string;
  warnings: { code: string; message: string; where?: string }[];
}

interface Emission {
  node: NodeJson;
  scope: Node;
}

const HTTP_HELPERS = new Set(["fetchApi", "fetchApiAuthenticated", "fetch"]);
const API_CLIENT_OBJECTS = new Set(["apiClient", "api"]);
const VERB_METHODS = new Set(["get", "post", "put", "delete", "patch"]);

function slugify(id: string): string {
  return id.replace(/::/g, "__").replace(/[^a-zA-Z0-9_]/g, "_").replace(/^_+|_+$/g, "");
}

function sha(payload: unknown): string {
  return crypto.createHash("sha256").update(JSON.stringify(payload)).digest("hex");
}

function gitHead(repo: string): string | null {
  const headPath = path.join(repo, ".git", "HEAD");
  if (!fs.existsSync(headPath)) return null;
  const ref = fs.readFileSync(headPath, "utf8").trim();
  if (ref.startsWith("ref:")) {
    const refFile = path.join(repo, ".git", ref.split(" ")[1]);
    if (fs.existsSync(refFile)) return fs.readFileSync(refFile, "utf8").trim().slice(0, 12);
  }
  return ref.slice(0, 12);
}

/** Replace ${...} with positional placeholders. Strip a single leading
 *  `${...}` if what follows starts with a slash — that's the `${API_BASE_URL}`
 *  prefix pattern in lib/api.ts. */
function canonicalizeUrl(raw: string): { path: string; fuzzy: boolean } | null {
  let i = 0;
  const fuzzy = /\$\{[^}]+\}/.test(raw);
  let canonical = raw.replace(/\$\{[^}]+\}/g, () => `{${i++}}`);
  canonical = canonical.replace(/^\{0\}(?=\/)/, "");
  if (!canonical.startsWith("/")) return null;
  if (canonical.includes("?")) canonical = canonical.split("?")[0];
  return { path: canonical, fuzzy };
}

function urlFromArg(arg: Node): { raw: string; fuzzy: boolean } | null {
  if (Node.isStringLiteral(arg)) return { raw: arg.getLiteralText(), fuzzy: false };
  if (Node.isNoSubstitutionTemplateLiteral(arg)) return { raw: arg.getLiteralText(), fuzzy: false };
  if (Node.isTemplateExpression(arg)) {
    const head = arg.getHead().getLiteralText();
    const spans = arg.getTemplateSpans().map((s) => "${EXPR}" + s.getLiteral().getLiteralText());
    return { raw: head + spans.join(""), fuzzy: true };
  }
  return null;
}

function methodFromOptions(arg: Node | undefined): string | null {
  if (!arg) return null;
  if (!Node.isObjectLiteralExpression(arg)) return null;
  for (const prop of arg.getProperties()) {
    if (!Node.isPropertyAssignment(prop)) continue;
    if (prop.getName() !== "method") continue;
    const init = prop.getInitializer();
    if (init && Node.isStringLiteral(init)) return init.getLiteralText().toUpperCase();
    if (init && Node.isNoSubstitutionTemplateLiteral(init)) return init.getLiteralText().toUpperCase();
  }
  return null;
}

/** Try to interpret a CallExpression as an HTTP call to /api/<...>.
 *  Returns null if the callee isn't a known helper or the URL doesn't resolve. */
function parseHttpCall(call: CallExpression): Edge | null {
  const expr = call.getExpression();
  let method: string | null = null;
  let urlArgIndex = 0;
  let optionsArgIndex = 1;

  if (Node.isIdentifier(expr)) {
    const name = expr.getText();
    if (!HTTP_HELPERS.has(name)) return null;
  } else if (Node.isPropertyAccessExpression(expr)) {
    const left = expr.getExpression().getText();
    const right = expr.getName();
    if (!API_CLIENT_OBJECTS.has(left) || !VERB_METHODS.has(right)) return null;
    method = right.toUpperCase();
  } else {
    return null;
  }

  const args = call.getArguments();
  if (args.length === 0) return null;
  const urlInfo = urlFromArg(args[urlArgIndex]);
  if (!urlInfo) return null;

  if (method === null) {
    method = methodFromOptions(args[optionsArgIndex]) ?? "GET";
  }

  const canon = canonicalizeUrl(urlInfo.raw);
  if (!canon) return null;
  if (!canon.path.startsWith("/api") && canon.path !== "/health") return null;

  const fuzzy = canon.fuzzy;
  return {
    target: `${method}::${canon.path}`,
    via: fuzzy ? "string_url" : "http_call",
    where: `${path.basename(call.getSourceFile().getFilePath())}:${call.getStartLineNumber()}`,
    confidence: fuzzy ? "fuzzy" : "exact",
  };
}

function makeNode(
  fullName: string,
  symbolNode: Node,
  sf: SourceFile,
  kind: "component" | "hook" | "service",
): NodeJson {
  const rel = path.relative(REPO, sf.getFilePath());
  // File-path-qualified id: prevents the same `SectionHeading` declared in three
  // different files from colliding on a single node JSON. See defect #11.
  const id = `${REPO_NAME}::${rel}::${fullName}`;
  const sigPayload = {
    name: fullName,
    kind,
    text: symbolNode.getText().slice(0, 1024), // bound the hash input; full body would explode for big components
  };
  return {
    schema_version: 1,
    id,
    kind,
    title: fullName,
    feature: null,
    source: { repo: REPO_NAME, path: rel, symbol: fullName, line: symbolNode.getStartLineNumber() },
    signature: { name: fullName, kind },
    structural_hash: sha(sigPayload),
    depends_on: [],
    external_consumers: [],
    tests: [],
    dossier: `dossiers/${kind === "hook" ? "hooks" : kind === "service" ? "services" : "components"}/${slugify(id)}.md`,
    extractor: "extract_web.ts",
    warnings: [],
  };
}

/** Decide what kind of node a top-level name represents. */
function classify(name: string): "component" | "hook" | "service" {
  if (/^use[A-Z]/.test(name)) return "hook";
  if (/^[A-Z]/.test(name)) return "component";
  return "service";
}

/** Object-literal property name: `service` kind regardless of casing,
 *  since these are typically API-helper methods (lowerCamelCase). */
function classifyMethod(_objName: string): "service" {
  return "service";
}

function buildEmissions(sf: SourceFile): Emission[] {
  const out: Emission[] = [];

  // 1. Function declarations (named) — exported, default-exported, OR named
  // top-level helpers. The latter matters for App Router page.tsx files where
  // the real logic lives in an inner `function PageContent()` and the default
  // export is just a Suspense wrapper.
  for (const decl of sf.getFunctions()) {
    const name = decl.getName();
    if (!name) continue;
    out.push({ node: makeNode(name, decl, sf, classify(name)), scope: decl });
  }

  // 2. Exported variable statements: arrow consts, object literals, function expressions
  for (const stmt of sf.getVariableStatements()) {
    if (!stmt.isExported()) continue;
    for (const varDecl of stmt.getDeclarations()) {
      const name = varDecl.getName();
      const init = varDecl.getInitializer();
      if (!name || !init) continue;

      if (Node.isArrowFunction(init) || Node.isFunctionExpression(init)) {
        out.push({ node: makeNode(name, varDecl, sf, classify(name)), scope: init });
        continue;
      }

      if (Node.isObjectLiteralExpression(init)) {
        for (const prop of init.getProperties()) {
          if (Node.isPropertyAssignment(prop)) {
            const propName = prop.getName();
            const propInit = prop.getInitializer();
            if (!propInit) continue;
            if (Node.isArrowFunction(propInit) || Node.isFunctionExpression(propInit)) {
              const fullName = `${name}.${propName}`;
              out.push({ node: makeNode(fullName, prop, sf, classifyMethod(name)), scope: propInit });
            }
          } else if (Node.isMethodDeclaration(prop)) {
            const propName = prop.getName();
            const fullName = `${name}.${propName}`;
            out.push({ node: makeNode(fullName, prop, sf, classifyMethod(name)), scope: prop });
          }
        }
      }
    }
  }

  return out;
}

/** For the page.tsx default-export pattern (`export default function Foo()`), the
 *  call sites we care about are inside Foo. But the page.tsx files this codebase
 *  uses also have an inner helper component (e.g. `function FooContent()`) that
 *  contains the actual handlers. To attribute those calls back to the exported
 *  default, we walk up parents and accept *any* non-exported function as a
 *  pass-through scope (i.e. we keep climbing). When we hit an emitted scope we
 *  stop and attribute. */
function findOwningEmission(call: Node, scopeSet: Map<Node, Emission>): Emission | null {
  let p: Node | undefined = call.getParent();
  while (p) {
    const hit = scopeSet.get(p);
    if (hit) return hit;
    p = p.getParent();
  }
  return null;
}

/** Collect imported names from the file so hook_call edges can resolve to a node
 *  id. Resolves the importing module to an actual file via ts-morph so the
 *  qualified id `<repo>::<file>::<symbol>` is correct. Imports that don't
 *  resolve to a file inside the repo (third-party packages, type-only modules,
 *  unresolved aliases) are skipped — they would never match a node anyway, and
 *  emitting them as phantom edges is worse than no edge. */
function buildImportMap(sf: SourceFile): Map<string, string> {
  const out = new Map<string, string>();
  for (const imp of sf.getImportDeclarations()) {
    const targetSf = imp.getModuleSpecifierSourceFile();
    if (!targetSf) continue;
    const targetFp = targetSf.getFilePath();
    if (targetFp.includes("node_modules")) continue;
    if (!targetFp.startsWith(REPO)) continue;
    const targetRel = path.relative(REPO, targetFp);

    for (const spec of imp.getNamedImports()) {
      const local = spec.getAliasNode()?.getText() ?? spec.getName();
      const importedName = spec.getName();
      out.set(local, `${REPO_NAME}::${targetRel}::${importedName}`);
    }
    const def = imp.getDefaultImport();
    if (def) {
      // Default exports are tricky: `export default function X` is named X in
      // the target file. ts-morph exposes default-export resolution, but for v1
      // we map to a `::default` placeholder. The emission for the actual
      // default-exported function uses its own name, so default-import edges
      // won't link until we resolve the real symbol. Documented limitation.
      out.set(def.getText(), `${REPO_NAME}::${targetRel}::default`);
    }
  }
  return out;
}

function attributeEdges(sf: SourceFile, emissions: Emission[]) {
  if (emissions.length === 0) return;
  const scopeSet = new Map(emissions.map((e) => [e.scope, e]));
  const importMap = buildImportMap(sf);

  sf.forEachDescendant((node) => {
    if (!Node.isCallExpression(node)) return;

    const owner = findOwningEmission(node, scopeSet);
    if (!owner) return;

    // HTTP edge?
    const httpEdge = parseHttpCall(node);
    if (httpEdge) {
      owner.node.depends_on.push(httpEdge);
      return;
    }

    // hook_call edge: call to an imported identifier or imported.method?
    // Targets are file-path-qualified ids resolved through buildImportMap so
    // they match the corresponding emission's id (defect #11 fix).
    const expr = node.getExpression();
    if (Node.isIdentifier(expr)) {
      const name = expr.getText();
      const target = importMap.get(name);
      if (target) {
        owner.node.depends_on.push({
          target,
          via: "hook_call",
          where: `${path.basename(sf.getFilePath())}:${node.getStartLineNumber()}`,
          confidence: "exact",
        });
      }
    } else if (Node.isPropertyAccessExpression(expr)) {
      const left = expr.getExpression().getText();
      const right = expr.getName();
      const importedLeft = importMap.get(left);
      if (importedLeft) {
        owner.node.depends_on.push({
          target: `${importedLeft}.${right}`,
          via: "hook_call",
          where: `${path.basename(sf.getFilePath())}:${node.getStartLineNumber()}`,
          confidence: "exact",
        });
      }
    }
  });
}

function dedupeEdges(edges: Edge[]): Edge[] {
  const seen = new Set<string>();
  const out: Edge[] = [];
  for (const e of edges) {
    const key = `${e.target}|${e.via}|${e.where}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(e);
  }
  return out;
}

/** Defect #4: per-node files no longer carry transient fields, so stableView
 *  is just the data with sorted keys for deterministic comparison. */
function stableView(obj: any): any {
  if (Array.isArray(obj)) return obj.map(stableView);
  if (obj === null || typeof obj !== "object") return obj;
  const out: Record<string, unknown> = {};
  for (const k of Object.keys(obj).sort()) {
    out[k] = stableView(obj[k]);
  }
  return out;
}

/** Write the node JSON only if its stable view differs from disk. Bit-stability:
 *  regen with no source change must not touch the file. Defect #2: atomic
 *  write via tmp+rename so a crash mid-write never leaves a half-written file. */
function writeNode(node: NodeJson): boolean {
  const subdir = node.kind === "hook" ? "hooks" : node.kind === "service" ? "services" : "components";
  const dir = path.join(NODES_DIR, subdir);
  fs.mkdirSync(dir, { recursive: true });
  const out = path.join(dir, `${slugify(node.id)}.json`);

  if (fs.existsSync(out)) {
    try {
      const existing = JSON.parse(fs.readFileSync(out, "utf8"));
      if (JSON.stringify(stableView(existing)) === JSON.stringify(stableView(node))) {
        return false;
      }
    } catch {
      // fall through and write
    }
  }
  const tmp = out + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(node, null, 2) + "\n");
  fs.renameSync(tmp, out);
  return true;
}

/** Defect #5: extractor manifests so reconciler can distinguish "source
 *  deleted" from "extractor skipped". Atomic write, bit-stable when ids are
 *  unchanged. */
function writeManifest(extractor: string, claimedIds: string[]) {
  const manifestDir = path.join(NODES_DIR, "_manifests");
  fs.mkdirSync(manifestDir, { recursive: true });
  const outPath = path.join(manifestDir, `${extractor}.json`);
  const payload = {
    schema_version: 1,
    extractor,
    generated_at: new Date().toISOString(),
    node_ids: [...claimedIds].sort(),
  };
  if (fs.existsSync(outPath)) {
    try {
      const existing = JSON.parse(fs.readFileSync(outPath, "utf8"));
      if (JSON.stringify(existing.node_ids) === JSON.stringify(payload.node_ids)) return;
    } catch {
      // fall through and write
    }
  }
  const tmp = outPath + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(payload, null, 2) + "\n");
  fs.renameSync(tmp, outPath);
}

function main() {
  const project = new Project({
    tsConfigFilePath: path.join(REPO, "tsconfig.json"),
    skipAddingFilesFromTsConfig: false,
  });

  let written = 0;
  let unchanged = 0;
  let edges = 0;
  let httpEdges = 0;
  const claimedIds: string[] = [];

  for (const sf of project.getSourceFiles()) {
    const fp = sf.getFilePath();
    if (fp.includes("node_modules")) continue;
    if (!fp.startsWith(REPO)) continue;

    const emissions = buildEmissions(sf);
    if (emissions.length === 0) continue;

    attributeEdges(sf, emissions);

    for (const e of emissions) {
      e.node.depends_on = dedupeEdges(e.node.depends_on);
      edges += e.node.depends_on.length;
      httpEdges += e.node.depends_on.filter((x) => x.via === "http_call" || x.via === "string_url").length;
      if (writeNode(e.node)) {
        written++;
      } else {
        unchanged++;
      }
      claimedIds.push(e.node.id);
    }
  }

  writeManifest("extract_web", claimedIds);
  console.log(
    `wrote ${written} web nodes (${unchanged} unchanged), ${edges} edges (${httpEdges} cross-HTTP), manifest=${claimedIds.length} ids`,
  );
}

main();
