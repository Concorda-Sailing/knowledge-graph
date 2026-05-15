/** Shared helpers for TypeScript detectors and the canonicalize stage.
 *  Ported byte-for-byte from pre-flip extract_web.ts / extract_tests.ts so
 *  the framework reproduces the same canonical output. */

import { Node, SyntaxKind, SourceFile, CallExpression } from "ts-morph";
import * as path from "node:path";

export const HTTP_HELPERS = new Set(["fetchApi", "fetchApiAuthenticated", "fetch"]);
export const API_CLIENT_OBJECTS = new Set(["apiClient", "api"]);
export const VERB_METHODS = new Set(["get", "post", "put", "delete", "patch"]);

export type EdgeVia =
  | "import"
  | "http_call"
  | "render"
  | "hook_call"
  | "string_url"
  | "test_fixture";

export type EdgeConfidence = "exact" | "fuzzy" | "inferred";

export interface Edge {
  target: string;
  via: EdgeVia;
  where: string;
  confidence: EdgeConfidence;
}

/** Replace ${...} with positional placeholders. Strip a single leading
 *  `${...}` if what follows starts with a slash — that's the `${API_BASE_URL}`
 *  prefix pattern in lib/api.ts. */
export function canonicalizeUrl(raw: string): { path: string; fuzzy: boolean } | null {
  let i = 0;
  const fuzzy = /\$\{[^}]+\}/.test(raw);
  let canonical = raw.replace(/\$\{[^}]+\}/g, () => `{${i++}}`);
  canonical = canonical.replace(/^\{0\}(?=\/)/, "");
  if (!canonical.startsWith("/")) return null;
  if (canonical.includes("?")) canonical = canonical.split("?")[0];
  return { path: canonical, fuzzy };
}

export function urlFromArg(arg: Node): { raw: string; fuzzy: boolean } | null {
  if (Node.isStringLiteral(arg)) return { raw: arg.getLiteralText(), fuzzy: false };
  if (Node.isNoSubstitutionTemplateLiteral(arg)) return { raw: arg.getLiteralText(), fuzzy: false };
  if (Node.isTemplateExpression(arg)) {
    const head = arg.getHead().getLiteralText();
    const spans = arg.getTemplateSpans().map((s) => "${EXPR}" + s.getLiteral().getLiteralText());
    return { raw: head + spans.join(""), fuzzy: true };
  }
  return null;
}

export function methodFromOptions(arg: Node | undefined): string | null {
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
export function parseHttpCall(call: CallExpression): Edge | null {
  const expr = call.getExpression();
  let method: string | null = null;
  const urlArgIndex = 0;
  const optionsArgIndex = 1;

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

/** Parse HTTP call for test code: `fetch(URL)`, `this.<verb>(URL)`,
 *  `this.request(METHOD, URL)`. Mirrors extract_tests.ts parseHttpCall. */
export function parseHttpCallTest(call: CallExpression): Edge | null {
  const expr = call.getExpression();
  let method: string | null = null;
  let urlArgIndex = 0;

  if (Node.isIdentifier(expr)) {
    if (expr.getText() !== "fetch") return null;
  } else if (Node.isPropertyAccessExpression(expr)) {
    const left = expr.getExpression();
    const right = expr.getName();
    if (left.getKind() === SyntaxKind.ThisKeyword && VERB_METHODS.has(right)) {
      method = right.toUpperCase();
    } else if (left.getKind() === SyntaxKind.ThisKeyword && right === "request") {
      const args = call.getArguments();
      if (args.length >= 2) {
        const methodArg = args[0];
        if (Node.isStringLiteral(methodArg)) {
          method = methodArg.getLiteralText().toUpperCase();
          urlArgIndex = 1;
        } else {
          return null;
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

/** Collect imported names from the file so hook_call/render edges can resolve
 *  to a node id. Resolves the importing module to an actual file via ts-morph
 *  so the qualified id `<repo>::<file>::<symbol>` is correct. Imports that
 *  don't resolve to a file inside the repo are skipped. */
export function buildImportMap(
  sf: SourceFile,
  repoKey: string,
  repoPath: string,
): Map<string, string> {
  const out = new Map<string, string>();
  for (const imp of sf.getImportDeclarations()) {
    const targetSf = imp.getModuleSpecifierSourceFile();
    if (!targetSf) continue;
    const targetFp = targetSf.getFilePath();
    if (targetFp.includes("node_modules")) continue;
    if (!targetFp.startsWith(repoPath)) continue;
    const targetRel = path.relative(repoPath, targetFp);

    for (const spec of imp.getNamedImports()) {
      const local = spec.getAliasNode()?.getText() ?? spec.getName();
      const importedName = spec.getName();
      out.set(local, `${repoKey}::${targetRel}::${importedName}`);
    }
    const def = imp.getDefaultImport();
    if (def) {
      out.set(def.getText(), `${repoKey}::${targetRel}::default`);
    }
  }
  return out;
}

/** Walk VariableDeclarations and pair `const x = new Y(...)` with the resolved
 *  qualified id of Y (when Y is imported). Maps `x → <repo>::<file>::Y` so a
 *  later `x.method()` call attributes correctly to the class method. */
export function buildInstanceMap(
  sf: SourceFile,
  importMap: Map<string, string>,
): Map<string, string> {
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

export function dedupeEdges(edges: Edge[]): Edge[] {
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
