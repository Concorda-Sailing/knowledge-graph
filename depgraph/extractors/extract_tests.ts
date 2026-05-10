#!/usr/bin/env -S npx tsx
/**
 * extract_tests.ts — walk concorda-test (Playwright) and emit:
 *   - test nodes (one per `test(...)`, `test.only`, `test.skip`, `test.fixme` call)
 *   - service nodes (every method on every class in lib/ and pages/)
 *   - exported function/arrow-const nodes (helpers in lib/test-data.ts etc.)
 *
 * Edges:
 *   - http_call : `this.<verb>('/api/...')` and `this.request(METHOD, URL)` inside
 *                 ApiClient methods → endpoint ids the api extractor emits
 *   - http_call : `fetch('/api/...')` and template-literal URLs (with the same
 *                 `${API_URL}/api/...` canonicalization web uses)
 *   - hook_call : imported.method() resolved via ts-morph's
 *                 getModuleSpecifierSourceFile() → file-path-qualified target
 *   - render    : page.goto(URL) when URL is a literal — left as fuzzy because
 *                 Next.js routes aren't extracted as nodes today
 *
 * The file shares structure with extract_web.ts (id format, write-if-changed,
 * canonicalUrl) but has Playwright-specific patterns: classes with methods,
 * test() call detection, and api-client-style HTTP wrappers using `this.`.
 */

import { Project, Node, SyntaxKind, SourceFile, CallExpression } from "ts-morph";
import * as crypto from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";

const REPO = process.env.CONCORDA_TEST_PATH ?? path.join(process.env.HOME!, "concorda-test");
const REPO_NAME = "concorda-test";
const DEPGRAPH = process.env.CONCORDA_DEPGRAPH_PATH ?? path.join(process.env.HOME!, "concorda", "depgraph");
const NODES_DIR = path.join(DEPGRAPH, "nodes");

type EdgeVia = "import" | "http_call" | "render" | "hook_call" | "string_url" | "test_fixture";
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
  kind: "test" | "service" | "component";
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

const TEST_VERBS = new Set(["only", "skip", "fixme"]);
const HTTP_VERBS = new Set(["get", "post", "put", "delete", "patch"]);
// Defect #4: no transient fields per-node; corpus-level meta lives elsewhere.

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

function stableView(obj: any): any {
  if (Array.isArray(obj)) return obj.map(stableView);
  if (obj === null || typeof obj !== "object") return obj;
  const out: Record<string, unknown> = {};
  for (const k of Object.keys(obj).sort()) {
    out[k] = stableView(obj[k]);
  }
  return out;
}

function canonicalizeUrl(raw: string): { path: string; fuzzy: boolean } | null {
  let i = 0;
  const fuzzy = /\$\{[^}]+\}/.test(raw);
  let canonical = raw.replace(/\$\{[^}]+\}/g, () => `{${i++}}`);
  // Test code uses ${API_URL}/api/... and ${this.baseUrl}/api/... — strip leading
  // placeholder if what follows starts with /
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

function parseHttpCall(call: CallExpression): Edge | null {
  const expr = call.getExpression();
  let method: string | null = null;
  let urlArgIndex = 0;

  if (Node.isIdentifier(expr)) {
    if (expr.getText() !== "fetch") return null;
    // method via options arg
  } else if (Node.isPropertyAccessExpression(expr)) {
    const left = expr.getExpression();
    const right = expr.getName();

    // this.get/post/put/delete/patch(URL, ...)
    if (left.getKind() === SyntaxKind.ThisKeyword && HTTP_VERBS.has(right)) {
      method = right.toUpperCase();
    }
    // this.request(METHOD, URL, ...)
    else if (left.getKind() === SyntaxKind.ThisKeyword && right === "request") {
      const args = call.getArguments();
      if (args.length >= 2) {
        const methodArg = args[0];
        if (Node.isStringLiteral(methodArg)) {
          method = methodArg.getLiteralText().toUpperCase();
          urlArgIndex = 1;
        } else {
          return null; // method passed dynamically
        }
      } else {
        return null;
      }
    } else {
      return null;
    }
  } else {
    return null;
  }

  const args = call.getArguments();
  if (args.length <= urlArgIndex) return null;
  const urlInfo = urlFromArg(args[urlArgIndex]);
  if (!urlInfo) return null;

  if (method === null) {
    // fetch options arg
    const optsArg = args[urlArgIndex + 1];
    if (optsArg && Node.isObjectLiteralExpression(optsArg)) {
      for (const prop of optsArg.getProperties()) {
        if (Node.isPropertyAssignment(prop) && prop.getName() === "method") {
          const init = prop.getInitializer();
          if (init && Node.isStringLiteral(init)) {
            method = init.getLiteralText().toUpperCase();
          }
        }
      }
    }
    if (method === null) method = "GET";
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
  kind: "test" | "service" | "component",
  titleOverride?: string,
): NodeJson {
  const rel = path.relative(REPO, sf.getFilePath());
  const id = `${REPO_NAME}::${rel}::${fullName}`;
  const sigPayload = {
    name: fullName,
    kind,
    text: symbolNode.getText().slice(0, 1024),
  };
  return {
    schema_version: 1,
    id,
    kind,
    title: titleOverride ?? fullName,
    feature: null,
    source: { repo: REPO_NAME, path: rel, symbol: fullName, line: symbolNode.getStartLineNumber() },
    signature: { name: fullName, kind },
    structural_hash: sha(sigPayload),
    depends_on: [],
    external_consumers: [],
    tests: [],
    dossier: `dossiers/${kind === "test" ? "tests" : kind === "service" ? "services" : "components"}/${slugify(id)}.md`,
    extractor: "extract_tests.ts",
    warnings: [],
  };
}

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
      out.set(local, `${REPO_NAME}::${targetRel}::${spec.getName()}`);
    }
    const def = imp.getDefaultImport();
    if (def) out.set(def.getText(), `${REPO_NAME}::${targetRel}::default`);
  }
  return out;
}

function isSpecFile(fp: string): boolean {
  return fp.endsWith(".spec.ts") || fp.endsWith(".spec.tsx");
}

function emitTestCalls(sf: SourceFile, out: Emission[]) {
  // Each `test('name', fn)`, `test.only('name', fn)`, etc. becomes a test node.
  // `test.describe(...)` is skipped — it's a grouping, not a leaf test.
  sf.forEachDescendant((node) => {
    if (!Node.isCallExpression(node)) return;
    const expr = node.getExpression();
    let isTest = false;
    if (Node.isIdentifier(expr) && expr.getText() === "test") {
      isTest = true;
    } else if (Node.isPropertyAccessExpression(expr)) {
      const left = expr.getExpression().getText();
      const right = expr.getName();
      if (left === "test" && TEST_VERBS.has(right)) isTest = true;
    }
    if (!isTest) return;

    const args = node.getArguments();
    if (args.length < 2) return;
    const nameArg = args[0];
    let title = "(unnamed)";
    if (Node.isStringLiteral(nameArg)) title = nameArg.getLiteralText();
    else if (Node.isNoSubstitutionTemplateLiteral(nameArg)) title = nameArg.getLiteralText();

    // The function body is the last argument (Playwright supports an options
    // arg between name and fn).
    const fnArg = args[args.length - 1];
    if (!Node.isArrowFunction(fnArg) && !Node.isFunctionExpression(fnArg)) return;

    const line = node.getStartLineNumber();
    const fullName = `test@${line}`;
    out.push({ node: makeNode(fullName, node, sf, "test", title), scope: fnArg });
  });
}

function emitClassMethods(sf: SourceFile, out: Emission[]) {
  for (const cls of sf.getClasses()) {
    const className = cls.getName();
    if (!className) continue;
    for (const m of cls.getMethods()) {
      const methodName = m.getName();
      if (!methodName) continue;
      // Skip private (lowercase prefixed _ in TS convention is informal; the
      // explicit `private` modifier is what we honor).
      if (m.getModifiers().some((mod) => mod.getText() === "private")) continue;
      const fullName = `${className}.${methodName}`;
      out.push({ node: makeNode(fullName, m, sf, "service"), scope: m });
    }
  }
}

function emitFunctionsAndConsts(sf: SourceFile, out: Emission[]) {
  for (const decl of sf.getFunctions()) {
    const name = decl.getName();
    if (!name) continue;
    out.push({ node: makeNode(name, decl, sf, "service"), scope: decl });
  }
  for (const stmt of sf.getVariableStatements()) {
    if (!stmt.isExported()) continue;
    for (const varDecl of stmt.getDeclarations()) {
      const name = varDecl.getName();
      const init = varDecl.getInitializer();
      if (!name || !init) continue;
      if (Node.isArrowFunction(init) || Node.isFunctionExpression(init)) {
        out.push({ node: makeNode(name, varDecl, sf, "service"), scope: init });
      } else if (Node.isObjectLiteralExpression(init)) {
        for (const prop of init.getProperties()) {
          if (Node.isPropertyAssignment(prop)) {
            const propInit = prop.getInitializer();
            if (propInit && (Node.isArrowFunction(propInit) || Node.isFunctionExpression(propInit))) {
              out.push({ node: makeNode(`${name}.${prop.getName()}`, prop, sf, "service"), scope: propInit });
            }
          }
        }
      }
    }
  }
}

function buildEmissions(sf: SourceFile): Emission[] {
  const out: Emission[] = [];
  emitFunctionsAndConsts(sf, out);
  emitClassMethods(sf, out);
  if (isSpecFile(sf.getFilePath())) {
    emitTestCalls(sf, out);
  }
  return out;
}

function findOwningEmission(call: Node, scopeSet: Map<Node, Emission>): Emission | null {
  let p: Node | undefined = call.getParent();
  while (p) {
    const hit = scopeSet.get(p);
    if (hit) return hit;
    p = p.getParent();
  }
  return null;
}

/** Walk VariableDeclarations and pair `const x = new Y(...)` with the resolved
 *  qualified id of Y (when Y is imported). Maps `x → <repo>::<file>::Y` so a
 *  later `x.method()` call attributes correctly to the class method.
 *  This is a simple file-level dataflow — wrong for re-bindings or shadowing,
 *  but in test code those are rare and the cost of a false attribution is just
 *  a phantom edge that doesn't resolve to a node. */
function buildInstanceMap(sf: SourceFile, importMap: Map<string, string>): Map<string, string> {
  const out = new Map<string, string>();
  sf.forEachDescendant((node) => {
    if (!Node.isVariableDeclaration(node)) return;
    const init = node.getInitializer();
    if (!init || !Node.isNewExpression(init)) return;
    const className = init.getExpression().getText();
    const target = importMap.get(className);
    if (!target) return;
    const name = node.getName();
    if (!name) return;
    out.set(name, target);
  });
  return out;
}

function attributeEdges(sf: SourceFile, emissions: Emission[]) {
  if (emissions.length === 0) return;
  const scopeSet = new Map(emissions.map((e) => [e.scope, e]));
  const importMap = buildImportMap(sf);
  const instanceMap = buildInstanceMap(sf, importMap);
  const baseName = path.basename(sf.getFilePath());

  sf.forEachDescendant((node) => {
    if (!Node.isCallExpression(node)) return;
    const owner = findOwningEmission(node, scopeSet);
    if (!owner) return;

    const httpEdge = parseHttpCall(node);
    if (httpEdge) {
      owner.node.depends_on.push(httpEdge);
      return;
    }

    const expr = node.getExpression();
    if (Node.isIdentifier(expr)) {
      const target = importMap.get(expr.getText());
      if (target) {
        owner.node.depends_on.push({
          target,
          via: "hook_call",
          where: `${baseName}:${node.getStartLineNumber()}`,
          confidence: "exact",
        });
      }
    } else if (Node.isPropertyAccessExpression(expr)) {
      const left = expr.getExpression().getText();
      const right = expr.getName();
      // Try instance map first (locally-bound `const x = new Y(...)`), then
      // imports. Instance match wins because importMap may also contain Y itself,
      // which would incorrectly resolve `x.method` to `Y.method` minus the
      // local binding context.
      const resolvedLeft = instanceMap.get(left) ?? importMap.get(left);
      if (resolvedLeft) {
        owner.node.depends_on.push({
          target: `${resolvedLeft}.${right}`,
          via: "hook_call",
          where: `${baseName}:${node.getStartLineNumber()}`,
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

function writeNode(node: NodeJson): boolean {
  const subdir = node.kind === "test" ? "tests" : node.kind === "service" ? "services" : "components";
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
  // Defect #2: atomic write — never leave a half-written JSON file.
  const tmp = out + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(node, null, 2) + "\n");
  fs.renameSync(tmp, out);
  return true;
}

/** Defect #5: extractor manifest emission. */
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
    } catch {}
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
  let testCount = 0;
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
      if (e.node.kind === "test") testCount++;
      if (writeNode(e.node)) {
        written++;
      } else {
        unchanged++;
      }
      claimedIds.push(e.node.id);
    }
  }

  writeManifest("extract_tests", claimedIds);
  console.log(
    `wrote ${written} test/svc nodes (${unchanged} unchanged), ${edges} edges (${httpEdges} cross-HTTP), tests: ${testCount}, manifest=${claimedIds.length} ids`,
  );
}

main();
