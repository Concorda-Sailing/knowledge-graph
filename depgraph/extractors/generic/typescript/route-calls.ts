#!/usr/bin/env tsx
/**
 * route-calls.ts — emit one `route_call` node per fetch() call site under --scan.
 *
 * Usage:
 *   npx tsx route-calls.ts --scan <dir> --repo-key <basename> [--base-url-var <name>]
 *
 * - --scan: directory to walk recursively for .ts/.tsx files.
 * - --repo-key: the repo basename used as the leading segment of the node id
 *   (must match a [repos.*].path basename in project.toml so reconcile resolves it).
 * - --base-url-var: optional. If a fetch URL starts with this template var
 *   (e.g. `${API_BASE_URL}/foo`), strip it. Defaults to API_BASE_URL.
 *
 * Emits NDJSON to stdout — one node per line.
 */

import * as ts from "typescript";
import * as fs from "fs";
import * as path from "path";

export const EXTRACTOR_VERSION = "1.0.0";

interface RouteCall {
  schema_version: 1;
  id: string;
  kind: "route_call";
  title: string;
  source: { repo: string; path: string; line: number };
  signature: { method: string; url_pattern: string | null };
  extractor: string;
  structural_hash: string;
  depends_on: never[];
}

function parseArgs(argv: string[]): { scan: string; repoKey: string; baseUrlVar: string } {
  const args = { scan: "", repoKey: "", baseUrlVar: "API_BASE_URL" };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--scan") args.scan = argv[++i];
    else if (argv[i] === "--repo-key") args.repoKey = argv[++i];
    else if (argv[i] === "--base-url-var") args.baseUrlVar = argv[++i];
  }
  if (!args.scan || !args.repoKey) {
    console.error("usage: route-calls.ts --scan <dir> --repo-key <basename> [--base-url-var <name>]");
    process.exit(2);
  }
  return args;
}

function* walk(dir: string): Generator<string> {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name.startsWith(".")) continue;
      yield* walk(full);
    } else if (entry.isFile() && /\.tsx?$/.test(entry.name)) {
      yield full;
    }
  }
}

function urlFromTemplate(node: ts.TemplateExpression, baseUrlVar: string): string | null {
  const parts: string[] = [];
  parts.push(node.head.text);
  for (const span of node.templateSpans) {
    const expr = span.expression;
    const isBaseUrl =
      ts.isIdentifier(expr) && expr.text === baseUrlVar && parts.length === 1 && parts[0] === "";
    if (isBaseUrl) {
      // Drop the leading base-URL placeholder.
    } else {
      parts.push("<var>");
    }
    parts.push(span.literal.text);
  }
  const url = parts.join("");
  return url || null;
}

function urlFromArg(arg: ts.Expression | undefined, baseUrlVar: string): string | null {
  if (!arg) return null;
  if (ts.isStringLiteral(arg) || ts.isNoSubstitutionTemplateLiteral(arg)) {
    return arg.text;
  }
  if (ts.isTemplateExpression(arg)) {
    return urlFromTemplate(arg, baseUrlVar);
  }
  return null;
}

function methodFromOpts(arg: ts.Expression | undefined): string {
  if (!arg || !ts.isObjectLiteralExpression(arg)) return "GET";
  for (const prop of arg.properties) {
    if (
      ts.isPropertyAssignment(prop) &&
      ts.isIdentifier(prop.name) &&
      prop.name.text === "method"
    ) {
      const v = prop.initializer;
      if (ts.isStringLiteral(v) || ts.isNoSubstitutionTemplateLiteral(v)) {
        return v.text.toUpperCase();
      }
    }
  }
  return "GET";
}

function symbolForCall(call: ts.CallExpression, sf: ts.SourceFile): string {
  let p: ts.Node | undefined = call.parent;
  while (p) {
    if (ts.isFunctionDeclaration(p) && p.name) return p.name.text;
    if (
      (ts.isVariableDeclaration(p) || ts.isPropertyAssignment(p)) &&
      ts.isIdentifier(p.name)
    )
      return p.name.text;
    if (ts.isMethodDeclaration(p) && ts.isIdentifier(p.name)) return p.name.text;
    p = p.parent;
  }
  const { line } = sf.getLineAndCharacterOfPosition(call.getStart(sf));
  return `fetch_at_${line + 1}`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const scanRoot = path.resolve(args.scan);
  const repoRoot = scanRoot.endsWith("/src") ? path.dirname(scanRoot) : scanRoot;

  for (const file of walk(scanRoot)) {
    const text = fs.readFileSync(file, "utf-8");
    const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true);

    function visit(node: ts.Node) {
      if (
        ts.isCallExpression(node) &&
        ts.isIdentifier(node.expression) &&
        node.expression.text === "fetch"
      ) {
        const url = urlFromArg(node.arguments[0], args.baseUrlVar);
        if (url !== null) {
          const method = methodFromOpts(node.arguments[1]);
          const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
          const symbol = symbolForCall(node, sf);
          const repoRelative = path.relative(repoRoot, file);
          const nodeId = `${args.repoKey}::${repoRelative}:${line + 1}::${symbol}`;

          const hashInput = `${method}|${url}|${args.repoKey}|${repoRelative}|${symbol}`;
          let h = 0;
          for (let i = 0; i < hashInput.length; i++) {
            h = (h * 31 + hashInput.charCodeAt(i)) | 0;
          }
          const structuralHash = (h >>> 0).toString(16).padStart(8, "0");

          const out: RouteCall = {
            schema_version: 1,
            id: nodeId,
            kind: "route_call",
            title: `fetch ${method} ${url}`,
            source: { repo: args.repoKey, path: repoRelative, line: line + 1 },
            signature: { method, url_pattern: url },
            extractor: "generic/typescript/route-calls",
            structural_hash: structuralHash,
            depends_on: [],
          };
          console.log(JSON.stringify(out));
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(sf);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
