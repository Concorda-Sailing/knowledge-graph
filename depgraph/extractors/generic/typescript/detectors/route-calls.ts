/** Route-call detector — emits a route_call canonical node for every
 *  HTTP call site that the shared parseHttpCall recognizes. Mirrors the
 *  pre-flip `generic/typescript/route-calls` extractor's slim schema:
 *  no dossier, no warnings, 8-char djb2-style hash, no symbol in source.
 *
 *  id format: `${repoKey}::${rel}:${line}::${symbol}`
 *    where `symbol` is the enclosing variable/function/method/property name
 *    (or `fetch_at_${line}` if no enclosing declaration is found).
 *
 *  structural_hash: 8-char djb2-style of `${method}|${url}|${repoKey}|${rel}|${symbol}`. */

import * as ts from "typescript";
import { Node } from "ts-morph";
import {
  Detector, DetectorContext, Mutation, Primitive,
} from "../detector_api.js";
import {
  HTTP_HELPERS, API_CLIENT_OBJECTS, VERB_METHODS,
  canonicalizeUrl, urlFromArg, methodFromOptions,
} from "./_shared.js";

function djb2Hex(input: string): string {
  let h = 0;
  for (let i = 0; i < input.length; i++) {
    h = (h * 31 + input.charCodeAt(i)) | 0;
  }
  return (h >>> 0).toString(16).padStart(8, "0");
}

function symbolForCall(call: import("ts-morph").CallExpression): string {
  // Walk parents to find the nearest enclosing named declaration: variable,
  // function, method, or property. Falls back to fetch_at_<line>.
  let p: Node | undefined = call.getParent();
  while (p) {
    if (Node.isFunctionDeclaration(p)) {
      const name = p.getName();
      if (name) return name;
    }
    if (Node.isVariableDeclaration(p) || Node.isPropertyAssignment(p)) {
      const nameNode = p.getNameNode();
      if (nameNode && Node.isIdentifier(nameNode)) return nameNode.getText();
    }
    if (Node.isMethodDeclaration(p)) {
      const nameNode = p.getNameNode();
      if (nameNode && Node.isIdentifier(nameNode)) return nameNode.getText();
    }
    p = p.getParent();
  }
  return `fetch_at_${call.getStartLineNumber()}`;
}

interface RouteCall {
  line: number;
  method: string;
  urlPattern: string;
  symbol: string;
}

function parseAsRoute(call: import("ts-morph").CallExpression): RouteCall | null {
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

  return {
    line: call.getStartLineNumber(),
    method,
    urlPattern: canon.path,
    symbol: symbolForCall(call),
  };
}

export class RouteCallsDetector implements Detector {
  name = "route-calls";

  detect(sf: ts.SourceFile, primitives: Primitive[], ctx: DetectorContext): Mutation[] {
    if (!ctx.tsMorphSf) return [];
    const tsf = ctx.tsMorphSf;
    const muts: Mutation[] = [];

    tsf.forEachDescendant((node) => {
      if (!Node.isCallExpression(node)) return;
      const rc = parseAsRoute(node);
      if (!rc) return;
      const id = `${ctx.repoKey}::${ctx.filePath}:${rc.line}::${rc.symbol}`;
      const signature = { method: rc.method, url_pattern: rc.urlPattern };
      const hashInput = `${rc.method}|${rc.urlPattern}|${ctx.repoKey}|${ctx.filePath}|${rc.symbol}`;
      const payload = {
        schema_version: 1,
        id,
        kind: "route_call",
        title: `fetch ${rc.method} ${rc.urlPattern}`,
        source: {
          repo: ctx.repoKey,
          path: ctx.filePath,
          line: rc.line,
        },
        signature,
        extractor: "generic/typescript/route-calls",
        structural_hash: djb2Hex(hashInput),
        depends_on: [],
      };
      muts.push({ type: "node", kind: "route_call", payload });
    });

    return muts;
  }
}
