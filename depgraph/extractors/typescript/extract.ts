/**
 * Layered-substrate TS extractor — emits primitives only.
 * Schema v2; see docs/superpowers/specs/2026-05-15-layered-substrate-design.md.
 */
import { Project, SourceFile, SyntaxKind, Node } from "ts-morph";
import { parseArgs } from "node:util";
import { readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { canonicalId, structuralHash } from "./canonical.js";

interface Primitive {
  schema_version: 2;
  id: string;
  primitive: "module" | "package" | "class" | "function" | "variable";
  name: string;
  owner: string | null;
  source: { repo: string; path: string; language: string; line: number; end_line: number };
  signature: any;
  attributes: any;
  edges_out: any[];
  structural_hash: string;
  // null for un-classified structural primitives. Some extraction passes
  // know the verdict up front (e.g. cross-repo route_call call sites) and
  // set it directly — `classify_corpus` honors extractor-set kind.
  kind: string | null;
  extractor: string;
}

const EXTRACTOR_TAG = "depgraph/extractors/typescript/extract.ts@2026-05-16";
const EXTS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"];

/**
 * Compile a path glob to a regex matching the full rel-path. Port of
 * `depgraph.lib.path_filters.compile_glob` — the two must stay in sync.
 *
 * Glob syntax (gitignore-flavoured):
 *   **\/  zero or more leading path segments (incl none)
 *   **    any characters, including `/`
 *   *     any characters except `/` (one segment)
 *   ?     any single character except `/`
 */
function compileGlob(pattern: string): RegExp {
  const pat = pattern.replace(/\\/g, "/").replace(/^\/+/, "");
  const parts: string[] = [];
  let i = 0;
  while (i < pat.length) {
    if (pat.slice(i, i + 3) === "**/") {
      parts.push("(?:.*/)?");
      i += 3;
    } else if (pat.slice(i, i + 2) === "**") {
      parts.push(".*");
      i += 2;
    } else if (pat[i] === "*") {
      parts.push("[^/]*");
      i += 1;
    } else if (pat[i] === "?") {
      parts.push("[^/]");
      i += 1;
    } else {
      parts.push(pat[i].replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
      i += 1;
    }
  }
  return new RegExp(`^${parts.join("")}$`);
}

function matchesAny(relPath: string, patterns: RegExp[]): boolean {
  const norm = relPath.replace(/\\/g, "/");
  return patterns.some((re) => re.test(norm));
}

/**
 * True if a repo-relative path is anywhere inside a `node_modules/` tree.
 *
 * ts-morph happily resolves `import {X} from "react-native"` *into*
 * `node_modules/react-native/types/index.d.ts` — that file isn't in the
 * filtered sourceFiles list (we skip it), but the resolved-source-file
 * pointer leaks through whenever ts-morph traces an import. Without
 * this guard, every external import becomes an edge with target
 * `<repo>::node_modules/.../foo.d.ts` — an in-corpus shape pointing at
 * a path we never extract, which `kg depgraph validate` correctly
 * flags as orphan (#29).
 */
export function inNodeModules(rel: string | null): boolean {
  if (!rel) return false;
  return rel.startsWith("node_modules/") || rel.includes("/node_modules/");
}

/**
 * Extract the npm package name from an import specifier.
 *
 *   "react"                       → "react"
 *   "react-native"                → "react-native"
 *   "@react-navigation/native"    → "@react-navigation/native"   (scope preserved)
 *   "@scope/pkg/sub/path"         → "@scope/pkg"
 *   "pkg/sub"                     → "pkg"
 *
 * Returns "local" for relative specs — callers should have routed those
 * to the relative-import path before reaching here; this is just a safe
 * fallback.
 */
export function npmPkgFromSpec(specText: string): string {
  if (specText.startsWith(".")) return "local";
  const parts = specText.split("/");
  if (parts[0].startsWith("@") && parts.length >= 2) {
    return `${parts[0]}/${parts[1]}`;
  }
  return parts[0];
}

/**
 * Extract the npm package name from a `node_modules/...` rel-path.
 *
 *   "node_modules/react/index.d.ts"                                       → "react"
 *   "node_modules/@react-navigation/native/lib/.../index.d.ts"           → "@react-navigation/native"
 *   "node_modules/@types/react/index.d.ts"                                → "react"  (DefinitelyTyped redirect)
 *
 * Returns null when the path isn't under node_modules at all.
 */
export function npmPkgFromNodeModulesRel(rel: string): string | null {
  if (!rel.startsWith("node_modules/")) return null;
  const parts = rel.split("/");
  if (parts.length < 2) return "unknown";
  if (parts[1] === "@types") return parts[2] || "unknown";
  if (parts[1].startsWith("@") && parts.length >= 3) {
    return `${parts[1]}/${parts[2]}`;
  }
  return parts[1];
}

function listSourceFiles(root: string): string[] {
  const out: string[] = [];
  function walk(dir: string) {
    for (const ent of readdirSync(dir)) {
      const p = join(dir, ent);
      const s = statSync(p);
      if (s.isDirectory()) {
        if (ent === "node_modules" || ent === ".git" || ent === "dist") continue;
        walk(p);
      } else if (EXTS.some((e) => p.endsWith(e))) {
        out.push(p);
      }
    }
  }
  walk(root);
  return out;
}

function emit(p: Primitive) {
  process.stdout.write(JSON.stringify(p) + "\n");
}

function moduleFor(sf: SourceFile, repoKey: string, repoPath: string): Primitive {
  const rel = relative(repoPath, sf.getFilePath());
  const id = `${repoKey}::${rel}`;
  return {
    schema_version: 2,
    id,
    primitive: "module",
    name: rel,
    owner: null,
    source: { repo: repoKey, path: rel, language: "typescript",
              line: 1, end_line: sf.getEndLineNumber() },
    signature: {},
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable: false,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({ kind: "module", path: rel }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function classPrimitive(
  node: Node,
  name: string,
  attrs: { abstract: boolean; instantiable: boolean; template_parameters: string[] },
  repoKey: string, relPath: string,
): Primitive {
  const id = canonicalId(repoKey, relPath, name);
  return {
    schema_version: 2,
    id,
    primitive: "class",
    name,
    owner: null,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line: node.getStartLineNumber(), end_line: node.getEndLineNumber() },
    signature: { decorators: [] },
    attributes: { abstract: attrs.abstract, generated: false, external: false,
                  template_parameters: attrs.template_parameters, macro: false,
                  mutable: false, instantiable: attrs.instantiable, inheritable: true },
    edges_out: [],
    structural_hash: structuralHash({ kind: "class", name, attrs }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function extractClasses(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];
  for (const cls of sf.getClasses()) {
    out.push(classPrimitive(cls, cls.getName() ?? "<anonymous>", {
      abstract: cls.isAbstract(),
      instantiable: !cls.isAbstract(),
      template_parameters: cls.getTypeParameters().map((tp) => tp.getName()),
    }, repoKey, relPath));
  }
  for (const iface of sf.getInterfaces()) {
    out.push(classPrimitive(iface, iface.getName(), {
      abstract: true, instantiable: false,
      template_parameters: iface.getTypeParameters().map((tp) => tp.getName()),
    }, repoKey, relPath));
  }
  for (const en of sf.getEnums()) {
    out.push(classPrimitive(en, en.getName(), {
      abstract: false, instantiable: false, template_parameters: [],
    }, repoKey, relPath));
  }
  for (const alias of sf.getTypeAliases()) {
    out.push(classPrimitive(alias, alias.getName(), {
      abstract: false, instantiable: false,
      template_parameters: alias.getTypeParameters().map((tp) => tp.getName()),
    }, repoKey, relPath));
  }
  return out;
}

function bodyHasJsx(node: { getDescendantsOfKind: (k: SyntaxKind) => any[] }): boolean {
  return (
    node.getDescendantsOfKind(SyntaxKind.JsxElement).length > 0 ||
    node.getDescendantsOfKind(SyntaxKind.JsxFragment).length > 0 ||
    node.getDescendantsOfKind(SyntaxKind.JsxSelfClosingElement).length > 0
  );
}

function bodyText(node: { getBodyText?: () => string | undefined; getText: () => string }): string {
  return (node.getBodyText?.() ?? node.getText()) || "";
}

function functionPrimitive(
  node: { getStartLineNumber(): number; getEndLineNumber(): number },
  name: string,
  owner: string | null,
  signature: { parameters: { name: string; type_annotation: string | null }[];
               return_type: string | null;
               is_async: boolean;
               decorators: string[];
               returns_jsx: boolean },
  body: string,
  repoKey: string, relPath: string,
): Primitive {
  const symbol = owner ? `${owner.split("::").pop()}.${name}` : name;
  const id = canonicalId(repoKey, relPath, symbol);
  return {
    schema_version: 2, id, primitive: "function", name: symbol, owner,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line: node.getStartLineNumber(), end_line: node.getEndLineNumber() },
    signature,
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable: false,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({ primitive: "function", name: symbol,
                                       signature, body_text: body }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function paramShape(p: any) {
  return { name: p.getName(), type_annotation: p.getTypeNode()?.getText() ?? null };
}

function moduleBasename(relPath: string): string {
  const last = relPath.split("/").pop() ?? relPath;
  const dot = last.lastIndexOf(".");
  return dot === -1 ? last : last.slice(0, dot);
}

function extractFunctions(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];

  for (const fn of sf.getFunctions()) {
    if (!fn.hasBody()) continue;
    const fnName = fn.getName() ?? `<default:${moduleBasename(relPath)}>`;
    out.push(functionPrimitive(fn, fnName, null, {
      parameters: fn.getParameters().map(paramShape),
      return_type: fn.getReturnTypeNode()?.getText() ?? null,
      is_async: fn.isAsync(),
      decorators: [],
      returns_jsx: bodyHasJsx(fn),
    }, bodyText(fn), repoKey, relPath));
  }

  for (const vs of sf.getVariableStatements()) {
    for (const decl of vs.getDeclarations()) {
      const init = decl.getInitializer();
      if (init && (Node.isArrowFunction(init) || Node.isFunctionExpression(init))) {
        out.push(functionPrimitive(decl, decl.getName(), null, {
          parameters: init.getParameters().map(paramShape),
          return_type: init.getReturnTypeNode()?.getText() ?? null,
          is_async: init.isAsync(),
          decorators: [],
          returns_jsx: bodyHasJsx(init),
        }, bodyText(init), repoKey, relPath));
      }
    }
  }

  // `export default function(){}` / `export default () => {}` are
  // ExportAssignment expressions whose expression is an anonymous fn.
  for (const ea of sf.getExportAssignments()) {
    if (ea.isExportEquals()) continue;
    const expr = ea.getExpression();
    if (Node.isFunctionExpression(expr) || Node.isArrowFunction(expr)) {
      if (Node.isFunctionExpression(expr) && expr.getName()) continue;
      const synthName = `<default:${moduleBasename(relPath)}>`;
      out.push(functionPrimitive(ea, synthName, null, {
        parameters: expr.getParameters().map(paramShape),
        return_type: expr.getReturnTypeNode()?.getText() ?? null,
        is_async: expr.isAsync(),
        decorators: [],
        returns_jsx: bodyHasJsx(expr),
      }, bodyText(expr), repoKey, relPath));
    }
  }

  for (const cls of sf.getClasses()) {
    const classId = canonicalId(repoKey, relPath, cls.getName() ?? "<anonymous>");
    for (const m of cls.getMethods()) {
      if (!m.hasBody()) continue;
      const methodLocalName = m.isStatic()
        ? `${m.getName()}:static`
        : m.getName();
      out.push(functionPrimitive(m, methodLocalName, classId, {
        parameters: m.getParameters().map(paramShape),
        return_type: m.getReturnTypeNode()?.getText() ?? null,
        is_async: m.isAsync(),
        decorators: m.getDecorators().map((d) => d.getName()),
        returns_jsx: bodyHasJsx(m),
      }, bodyText(m), repoKey, relPath));
    }
  }

  return out;
}

function variablePrimitive(
  node: { getStartLineNumber(): number; getEndLineNumber(): number },
  name: string, owner: string | null, mutable: boolean,
  type_annotation: string | null,
  value_text: string | null,
  repoKey: string, relPath: string,
): Primitive {
  const symbol = owner ? `${owner.split("::").pop()}.${name}` : name;
  const signature = { type_annotation, value_text };
  return {
    schema_version: 2, id: canonicalId(repoKey, relPath, symbol),
    primitive: "variable", name: symbol, owner,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line: node.getStartLineNumber(), end_line: node.getEndLineNumber() },
    signature,
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({
      primitive: "variable", name: symbol,
      signature, body_text: value_text ?? "",
    }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  };
}

function extractVariables(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];

  for (const vs of sf.getVariableStatements()) {
    const declKind = vs.getDeclarationKind();  // "const" | "let" | "var"
    for (const decl of vs.getDeclarations()) {
      const init = decl.getInitializer();
      if (init && (Node.isArrowFunction(init) || Node.isFunctionExpression(init))) continue;
      // Also skip object literals — handled by extractObjectLiteralApiClients
      if (init && Node.isObjectLiteralExpression(init)) continue;
      out.push(variablePrimitive(decl, decl.getName(), null,
        declKind !== "const",
        decl.getTypeNode()?.getText() ?? null,
        init?.getText() ?? null,
        repoKey, relPath));
    }
  }

  for (const cls of sf.getClasses()) {
    const classId = canonicalId(repoKey, relPath, cls.getName() ?? "<anonymous>");
    for (const prop of cls.getProperties()) {
      out.push(variablePrimitive(prop, prop.getName(), classId,
        !prop.isReadonly(),
        prop.getTypeNode()?.getText() ?? null,
        prop.getInitializer()?.getText() ?? null,
        repoKey, relPath));
    }
  }

  return out;
}

function packagePrimitives(sourceFiles: SourceFile[], repoKey: string, repoPath: string): Primitive[] {
  const dirs = new Set<string>();
  for (const sf of sourceFiles) {
    let rel = relative(repoPath, sf.getFilePath());
    let dir = rel.includes("/") ? rel.substring(0, rel.lastIndexOf("/")) : "";
    while (dir) {
      dirs.add(dir);
      dir = dir.includes("/") ? dir.substring(0, dir.lastIndexOf("/")) : "";
    }
    if (dirs.has("")) dirs.delete("");
  }
  return [...dirs].sort().map((d) => ({
    schema_version: 2 as const,
    id: `${repoKey}::${d}`,
    primitive: "package" as const,
    name: d,
    owner: null,
    source: { repo: repoKey, path: d, language: "typescript", line: 0, end_line: 0 },
    signature: {},
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable: false,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({ kind: "package", path: d }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  }));
}

function extractObjectLiteralApiClients(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  const out: Primitive[] = [];
  for (const vs of sf.getVariableStatements()) {
    for (const decl of vs.getDeclarations()) {
      const init = decl.getInitializer();
      if (!init || !Node.isObjectLiteralExpression(init)) continue;
      const className = decl.getName();
      const classId = canonicalId(repoKey, relPath, className);
      out.push({
        schema_version: 2, id: classId, primitive: "class",
        name: className, owner: null,
        source: { repo: repoKey, path: relPath, language: "typescript",
                  line: decl.getStartLineNumber(), end_line: decl.getEndLineNumber() },
        signature: {},
        attributes: { abstract: false, generated: false, external: false,
                      template_parameters: [], macro: false, mutable: false,
                      instantiable: true, inheritable: false },
        edges_out: [],
        structural_hash: structuralHash({ kind: "class", name: className, object_literal: true }),
        kind: null,
        extractor: EXTRACTOR_TAG,
      });

      for (const prop of init.getProperties()) {
        if (Node.isMethodDeclaration(prop) || (Node.isPropertyAssignment(prop) &&
            (Node.isArrowFunction(prop.getInitializer()!) || Node.isFunctionExpression(prop.getInitializer()!)))) {
          const isMethod = Node.isMethodDeclaration(prop);
          const memberName = isMethod ? prop.getName() : (prop as any).getName();
          const fnNode: any = isMethod ? prop : (prop as any).getInitializer()!;
          out.push(functionPrimitive(fnNode, memberName, classId, {
            parameters: fnNode.getParameters().map(paramShape),
            return_type: fnNode.getReturnTypeNode?.()?.getText() ?? null,
            is_async: fnNode.isAsync?.() ?? false,
            decorators: [],
            returns_jsx: bodyHasJsx(fnNode),
          }, bodyText(fnNode), repoKey, relPath));
        } else if (Node.isPropertyAssignment(prop)) {
          const initText = (prop as any).getInitializer()?.getText() ?? null;
          out.push(variablePrimitive(prop, prop.getName(), classId, true,
            null, initText, repoKey, relPath));
        }
      }
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// L2 edge resolution — Task 3.1: defines
// ---------------------------------------------------------------------------

function attachDefinesEdges(prims: Primitive[]): void {
  for (const p of prims) {
    if (p.primitive === "module") {
      for (const child of prims) {
        if (child.id === p.id) continue;
        if (
          child.source.path === p.source.path &&
          child.owner === null &&
          (child.primitive === "class" ||
            child.primitive === "function" ||
            child.primitive === "variable")
        ) {
          p.edges_out.push({
            target: child.id,
            kind: "defines",
            via: "lexical_scope",
            where: `${p.source.path}:${child.source.line}`,
            confidence: "exact",
          });
        }
      }
    } else if (p.primitive === "class") {
      for (const child of prims) {
        if (child.owner === p.id) {
          p.edges_out.push({
            target: child.id,
            kind: "defines",
            via: "class_body",
            where: `${p.source.path}:${child.source.line}`,
            confidence: "exact",
          });
        }
      }
    } else if (p.primitive === "package") {
      for (const child of prims) {
        if (child.primitive !== "module") continue;
        const childPath = child.source.path;
        const childDir = childPath.includes("/")
          ? childPath.substring(0, childPath.lastIndexOf("/"))
          : "";
        if (childDir === p.source.path) {
          p.edges_out.push({
            target: child.id,
            kind: "defines",
            via: "package_member",
            where: `${p.source.path}/`,
            confidence: "exact",
          });
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------
// L2 edge resolution — Task 3.2: extends / implements
// ---------------------------------------------------------------------------

function buildLocalSymbolIndex(prims: Primitive[]): Map<string, string> {
  const idx = new Map<string, string>();
  for (const p of prims) {
    if (
      p.owner === null &&
      (p.primitive === "class" ||
        p.primitive === "function" ||
        p.primitive === "variable")
    ) {
      idx.set(p.name, p.id);
    }
  }
  return idx;
}

function attachInheritanceEdges(
  prims: Primitive[],
  sourceFiles: SourceFile[],
  repoKey: string,
  repoPath: string,
): void {
  const symbolIndex = buildLocalSymbolIndex(prims);
  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    for (const cls of sf.getClasses()) {
      const clsName = cls.getName() ?? "<anonymous>";
      const myId = canonicalId(repoKey, rel, clsName);
      const myPrim = prims.find((p) => p.id === myId);
      if (!myPrim) continue;

      const exClause = cls.getExtends();
      if (exClause) {
        const targetName = exClause.getExpression().getText();
        const targetId = symbolIndex.get(targetName);
        if (targetId) {
          myPrim.edges_out.push({
            target: targetId,
            kind: "extends",
            via: "class_decl",
            where: `${rel}:${exClause.getStartLineNumber()}`,
            confidence: "exact",
          });
        }
      }

      for (const impl of cls.getImplements()) {
        const targetName = impl.getExpression().getText();
        const targetId = symbolIndex.get(targetName);
        if (targetId) {
          myPrim.edges_out.push({
            target: targetId,
            kind: "implements",
            via: "class_decl",
            where: `${rel}:${impl.getStartLineNumber()}`,
            confidence: "exact",
          });
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------
// L2 edge resolution — Task 3.3: imports
// ---------------------------------------------------------------------------

function resolveRelativeImportSpec(
  fromRel: string,
  spec: string,
  modByPath: Map<string, Primitive>,
): string | null {
  const lastSlash = fromRel.lastIndexOf("/");
  const fromDir = lastSlash >= 0 ? fromRel.slice(0, lastSlash) : "";
  const parts = [...fromDir.split("/").filter(Boolean), ...spec.split("/")];
  const stack: string[] = [];
  for (const p of parts) {
    if (p === "." || p === "") continue;
    if (p === "..") { stack.pop(); continue; }
    stack.push(p);
  }
  const base = stack.join("/");
  const hasKnownExt = /\.(ts|tsx|js|jsx|mjs|cjs)$/.test(base);
  const candidates: string[] = [];
  if (hasKnownExt) candidates.push(base);
  for (const ext of EXTS) candidates.push(`${base}${ext}`);
  for (const ext of EXTS) candidates.push(`${base}/index${ext}`);
  // Authors writing TS-resolves-via-extension (`./foo.js` that points at
  // `./foo.ts` on disk) are common — try swapping known extensions too.
  if (hasKnownExt) {
    const stem = base.replace(/\.(ts|tsx|js|jsx|mjs|cjs)$/, "");
    for (const ext of EXTS) candidates.push(`${stem}${ext}`);
  }
  for (const c of candidates) {
    if (modByPath.has(c)) return c;
  }
  return null;
}

function attachImportsEdges(
  prims: Primitive[],
  sourceFiles: SourceFile[],
  repoKey: string,
  repoPath: string,
): void {
  // Build symbol index: symbol name -> id (top-level, owner-null)
  const symbolIndex = buildLocalSymbolIndex(prims);
  // Build module map: rel-path -> primitive
  const modByPath = new Map<string, Primitive>();
  for (const p of prims) {
    if (p.primitive === "module") modByPath.set(p.source.path, p);
  }
  // Build per-module symbol map: rel-path -> {name -> id}
  const symByPath = new Map<string, Map<string, string>>();
  for (const p of prims) {
    if (p.owner === null && p.primitive !== "module" && p.primitive !== "package") {
      if (!symByPath.has(p.source.path)) symByPath.set(p.source.path, new Map());
      symByPath.get(p.source.path)!.set(p.name, p.id);
    }
  }

  // Build re-export map: module rel-path -> {exportedName -> origin-symbol-id}.
  // Two-phase build: first collect each file's named re-exports and the set
  // of files it re-exports wholesale via `export * from './x'`. Then expand
  // wildcards via DFS so a consumer's lookup against a barrel that only does
  // `export *` still resolves to the underlying definer. A final closure
  // pass collapses chains of synthetic placeholders left by named-only
  // multi-hop chains.
  const namedReexports = new Map<string, Map<string, string>>();
  const wildcardFrom = new Map<string, Set<string>>();
  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    for (const exp of sf.getExportDeclarations()) {
      if (!exp.hasModuleSpecifier()) continue;
      const targetSf2 = exp.getModuleSpecifierSourceFile();
      let targetRel2 = targetSf2 ? relative(repoPath, targetSf2.getFilePath()) : null;
      // ts-morph resolves package imports into node_modules type stubs;
      // those aren't in-corpus modules — don't track them as such (#29).
      if (inNodeModules(targetRel2)) targetRel2 = null;
      if (!targetRel2) continue;
      const named = exp.getNamedExports();
      // `export * from './x'` (no named exports, no namespace alias) — record
      // the wildcard relationship; symbol enumeration happens in the DFS.
      if (named.length === 0 && !exp.getNamespaceExport()) {
        if (!wildcardFrom.has(rel)) wildcardFrom.set(rel, new Set());
        wildcardFrom.get(rel)!.add(targetRel2);
        continue;
      }
      const targetSyms2 = symByPath.get(targetRel2) ?? new Map();
      for (const spec of named) {
        const exportedName = spec.getName();
        const aliasNode = spec.getAliasNode();
        // For `export { foo as bar } from './x'`, consumers see `bar` — that
        // is the key in our map. `spec.getName()` returns the local name
        // (`foo`), which is what we look up in the target file.
        const consumerName = aliasNode ? aliasNode.getText() : exportedName;
        const symId = targetSyms2.get(exportedName);
        const originId = symId ?? `${repoKey}::${targetRel2}::${exportedName}`;
        if (!namedReexports.has(rel)) namedReexports.set(rel, new Map());
        namedReexports.get(rel)!.set(consumerName, originId);
      }
    }
  }

  // DFS: effective exports of `file` = direct definitions ∪ named re-exports
  // ∪ wildcard targets' effective exports. Named/direct entries win on key
  // collision (matches TS semantics). `visiting` breaks cycles.
  function effectiveExports(file: string, visiting: Set<string>): Map<string, string> {
    if (visiting.has(file)) return new Map();
    visiting.add(file);
    const out = new Map<string, string>();
    const direct = symByPath.get(file);
    if (direct) for (const [k, v] of direct) out.set(k, v);
    const ne = namedReexports.get(file);
    if (ne) for (const [k, v] of ne) if (!out.has(k)) out.set(k, v);
    const wts = wildcardFrom.get(file);
    if (wts) {
      for (const wt of wts) {
        const wtExports = effectiveExports(wt, visiting);
        for (const [k, v] of wtExports) if (!out.has(k)) out.set(k, v);
      }
    }
    visiting.delete(file);
    return out;
  }

  const reexportMap = new Map<string, Map<string, string>>();
  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    const ne = namedReexports.get(rel);
    const wts = wildcardFrom.get(rel);
    if (!ne && !wts) continue;
    const map = new Map<string, string>();
    if (ne) for (const [k, v] of ne) map.set(k, v);
    if (wts) {
      for (const wt of wts) {
        const wtExports = effectiveExports(wt, new Set([rel]));
        for (const [k, v] of wtExports) if (!map.has(k)) map.set(k, v);
      }
    }
    reexportMap.set(rel, map);
  }

  // Closure pass: for each entry whose synthetic target points at a file
  // that itself re-exports the same name, replace with the deeper origin.
  // Bounded depth prevents infinite loops on cyclic barrels.
  const MAX_REEXPORT_HOPS = 16;
  for (const exports of reexportMap.values()) {
    for (const [name, id] of exports) {
      let resolved = id;
      for (let hop = 0; hop < MAX_REEXPORT_HOPS; hop++) {
        // Parse `<repo>::<file>::<name>` shape. Bail on anything else
        // (e.g. external terminals, module-only ids).
        const idx = resolved.indexOf("::");
        if (idx < 0) break;
        const rest = resolved.slice(idx + 2);
        const innerIdx = rest.lastIndexOf("::");
        if (innerIdx < 0) break;
        const innerFile = rest.slice(0, innerIdx);
        const innerName = rest.slice(innerIdx + 2);
        // If innerFile defines innerName as a real primitive, we're done.
        if (symByPath.get(innerFile)?.has(innerName)) break;
        const nextHop = reexportMap.get(innerFile)?.get(innerName);
        if (!nextHop || nextHop === resolved) break;
        resolved = nextHop;
      }
      if (resolved !== id) exports.set(name, resolved);
    }
  }

  // Default-export alias map: file -> primitive id named by `export default X`
  // (where X is an identifier resolving to a same-file symbol, or a top-level
  // declaration with the `default` modifier). Lets `import X from './m'`
  // resolve to the real symbol rather than the synthetic `default` id.
  const defaultExportMap = new Map<string, string>();
  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    const localSyms = symByPath.get(rel);
    if (!localSyms) continue;
    for (const ea of sf.getExportAssignments()) {
      if (ea.isExportEquals()) continue;
      const expr = ea.getExpression();
      if (Node.isIdentifier(expr)) {
        const id = localSyms.get(expr.getText());
        if (id) defaultExportMap.set(rel, id);
      }
    }
    if (defaultExportMap.has(rel)) continue;
    for (const cls of sf.getClasses()) {
      if (cls.hasDefaultKeyword()) {
        const name = cls.getName();
        const id = name ? localSyms.get(name) : undefined;
        if (id) { defaultExportMap.set(rel, id); break; }
      }
    }
    if (defaultExportMap.has(rel)) continue;
    for (const fn of sf.getFunctions()) {
      if (fn.hasDefaultKeyword()) {
        const name = fn.getName();
        const id = name ? localSyms.get(name) : undefined;
        if (id) { defaultExportMap.set(rel, id); break; }
      }
    }
  }

  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    const modPrim = modByPath.get(rel);
    if (!modPrim) continue;

    for (const imp of sf.getImportDeclarations()) {
      // Try to resolve the module specifier file via ts-morph
      const targetSf = imp.getModuleSpecifierSourceFile();
      let targetRel = targetSf ? relative(repoPath, targetSf.getFilePath()) : null;
      // If ts-morph traced the import into a node_modules type stub
      // (`react-native` → `node_modules/react-native/types/index.d.ts`),
      // treat as external — those files aren't in the corpus and we
      // shouldn't emit in-corpus edges to them (#29).
      if (inNodeModules(targetRel)) targetRel = null;
      const targetSyms = targetRel ? (symByPath.get(targetRel) ?? new Map()) : new Map();
      const targetReexports = targetRel ? (reexportMap.get(targetRel) ?? new Map()) : new Map();

      const defaultImport = imp.getDefaultImport();
      if (defaultImport) {
        const localBinding = defaultImport.getText();
        const defaultId = targetRel ? defaultExportMap.get(targetRel) : undefined;
        const externalPkg = npmPkgFromSpec(imp.getModuleSpecifierValue());
        const target = defaultId
          ? defaultId
          : targetRel
            ? `${repoKey}::${targetRel}::default`
            : `external::npm::${externalPkg}::default`;  // #29
        const confidence = defaultId
          ? "fuzzy"
          : (targetRel ? "exact" : "unresolved");
        modPrim.edges_out.push({
          target, kind: "imports", via: "import_decl",
          where: `${rel}:${imp.getStartLineNumber()}`,
          confidence, local_binding: localBinding,
        });
      }

      const nsImport = imp.getNamespaceImport();
      if (nsImport) {
        const localBinding = nsImport.getText();
        const externalPkg = npmPkgFromSpec(imp.getModuleSpecifierValue());
        const target = targetRel
          ? `${repoKey}::${targetRel}`
          : `external::npm::${externalPkg}`;  // #29
        const confidence = targetRel ? "exact" : "unresolved";
        modPrim.edges_out.push({
          target, kind: "imports", via: "import_decl",
          where: `${rel}:${imp.getStartLineNumber()}`,
          confidence, local_binding: localBinding,
        });
      }

      for (const spec of imp.getNamedImports()) {
        const importedName = spec.getName();
        const aliasNode = spec.getAliasNode();
        const localBinding = aliasNode ? aliasNode.getText() : importedName;

        let target: string;
        let confidence: string;
        if (targetRel) {
          const symId = targetSyms.get(importedName);
          if (symId) {
            target = symId;
            confidence = "exact";
          } else {
            // One-hop re-export chase: symbol may be re-exported from another module
            const reexportId = targetReexports.get(importedName);
            if (reexportId) {
              target = reexportId;
              confidence = "fuzzy";
            } else {
              // Couldn't resolve to the named symbol. Falling back to the
              // module id is the best we can do, but the resolution is a
              // guess — not "exact." Downgrade to "fuzzy" so consumers know
              // the edge is module-level rather than symbol-level.
              target = `${repoKey}::${targetRel}`;
              confidence = "fuzzy";
            }
          }
        } else {
          // Unresolved external (or resolved-into-node_modules, which we
          // just demoted to `targetRel = null` above). Use the import
          // specifier to derive the npm package name so scoped packages
          // keep their scope: `@react-navigation/native::ScreenProps`
          // rather than the lossy `react-navigation::ScreenProps` (#29).
          const specText = imp.getModuleSpecifierValue();
          const pkgName = npmPkgFromSpec(specText);
          target = `external::npm::${pkgName}::${importedName}`;
          confidence = "unresolved";
        }
        modPrim.edges_out.push({
          target, kind: "imports", via: "import_decl",
          where: `${rel}:${imp.getStartLineNumber()}`,
          confidence, local_binding: localBinding,
        });
      }
    }

    // Re-exports: export { foo } from "./impl.js"
    for (const exp of sf.getExportDeclarations()) {
      if (!exp.hasModuleSpecifier()) continue;
      const targetSf2 = exp.getModuleSpecifierSourceFile();
      let targetRel2 = targetSf2 ? relative(repoPath, targetSf2.getFilePath()) : null;
      if (inNodeModules(targetRel2)) targetRel2 = null;  // #29
      const targetSyms2 = targetRel2 ? (symByPath.get(targetRel2) ?? new Map()) : new Map();
      const targetReexports2 = targetRel2 ? (reexportMap.get(targetRel2) ?? new Map()) : new Map();

      const externalPkg = npmPkgFromSpec(exp.getModuleSpecifierValue() || "");
      for (const spec of exp.getNamedExports()) {
        const exportedName = spec.getName();
        const aliasNode = spec.getAliasNode();
        const localBinding = aliasNode ? aliasNode.getText() : exportedName;
        const symId = targetRel2 ? targetSyms2.get(exportedName) : undefined;
        // Chase through the target file's own re-exports (the closure pass
        // above has already collapsed multi-hop chains, so one lookup here
        // suffices).
        const reexportId = targetRel2 ? targetReexports2.get(exportedName) : undefined;
        const target = symId
          ? symId
          : reexportId
            ? reexportId
            : targetRel2
              ? `${repoKey}::${targetRel2}::${exportedName}`
              : `external::npm::${externalPkg}::${exportedName}`;  // #29
        modPrim.edges_out.push({
          target, kind: "imports", via: "re_export",
          where: `${rel}:${exp.getStartLineNumber()}`,
          confidence: "fuzzy", local_binding: localBinding,
        });
      }
    }

    // Plain dynamic imports: `await import('./rel')` or `await import('pkg')`.
    // Attributed to the enclosing module (same as static imports), so impact
    // analysis and `kg depgraph dependents` see them. The Function-constructor
    // shim form is handled separately in attachCallEdges.
    //
    // Visitor walk rather than getDescendantsOfKind so the CallExpression
    // descendant array is never materialized — #44 traced an RSS spike to that
    // allocation.
    sf.forEachDescendant((node) => {
      if (!Node.isCallExpression(node)) return;
      const call = node;
      if (call.getExpression().getKind() !== SyntaxKind.ImportKeyword) return;
      const args = call.getArguments();
      if (args.length === 0) return;
      const first = args[0];
      // Non-literal spec (template w/ interpolation, identifier, etc.) — can't
      // resolve statically. Skip rather than emit a wrong edge.
      if (!Node.isStringLiteral(first) && !Node.isNoSubstitutionTemplateLiteral(first)) return;
      const specText = (first as any).getLiteralText();
      let target: string;
      let confidence: "exact" | "fuzzy" | "unresolved";
      if (specText.startsWith(".")) {
        const resolved = resolveRelativeImportSpec(rel, specText, modByPath);
        if (resolved) {
          target = `${repoKey}::${resolved}`;
          confidence = "exact";
        } else {
          target = `external::unresolved::${specText}`;
          confidence = "unresolved";
        }
      } else {
        target = `external::npm::${npmPkgFromSpec(specText)}`;  // #29
        confidence = "fuzzy";
      }
      modPrim.edges_out.push({
        target, kind: "imports", via: "dynamic_import",
        where: `${rel}:${call.getStartLineNumber()}`, confidence,
      });
    });
  }
}

// ---------------------------------------------------------------------------
// L2 edge resolution — Task 3.4/3.5: calls + instantiates (intra-fn type
// binding) + reads/assigns. Combined into a single per-function descendant
// walk so the AST is traversed once per fn instead of twice (#44 — fewer
// resident ts-morph wrapper nodes at any moment).
// ---------------------------------------------------------------------------

function attachCallAndVarAccessEdges(
  prims: Primitive[],
  sourceFiles: SourceFile[],
  repoKey: string,
  repoPath: string,
): void {
  const classesByPath = new Map<string, Map<string, Primitive>>();
  const methodsByClass = new Map<string, Map<string, string>>(); // classId -> {methodName -> fnId}
  const fnByPathAndLine = new Map<string, Primitive>(); // "path:line" -> prim
  const modByPath = new Map<string, Primitive>();
  const varsByPath = new Map<string, Map<string, string>>(); // path -> name -> varId (module-scope)
  for (const p of prims) {
    if (p.primitive === "module") modByPath.set(p.source.path, p);
    if (p.primitive === "variable" && p.owner === null) {
      if (!varsByPath.has(p.source.path)) varsByPath.set(p.source.path, new Map());
      varsByPath.get(p.source.path)!.set(p.name, p.id);
    }
  }

  for (const p of prims) {
    if (p.primitive === "class" && p.owner === null) {
      if (!classesByPath.has(p.source.path))
        classesByPath.set(p.source.path, new Map());
      classesByPath.get(p.source.path)!.set(p.name, p);
    }
    if (p.primitive === "function") {
      fnByPathAndLine.set(`${p.source.path}:${p.source.line}`, p);
      if (p.owner !== null) {
        if (!methodsByClass.has(p.owner)) methodsByClass.set(p.owner, new Map());
        // method name is last segment after dot
        const localName = p.name.split(".").pop()!;
        // strip :static suffix for lookup
        const lookupName = localName.replace(/:static$/, "");
        methodsByClass.get(p.owner)!.set(lookupName, p.id);
      }
    }
  }

  // Primitive-kind index for taxonomy-correct edge emission. `calls` targets
  // must be functions and `instantiates` targets must be classes (per
  // depgraph/lib/edges.py::EDGE_KIND_RULES); a bare-id call site can resolve
  // to a variable holding a callable, in which case no `calls` edge is
  // emitted and the identifier-read pass picks up the relationship as a
  // `reads function→variable` edge.
  const allClassIds = new Set(prims.filter((p) => p.primitive === "class").map((p) => p.id));
  const allFunctionIds = new Set(prims.filter((p) => p.primitive === "function").map((p) => p.id));

  // Local top-level symbol index per file: name -> id (non-method, owner-null)
  const localByPath = new Map<string, Map<string, string>>();
  for (const p of prims) {
    if (p.owner === null && (p.primitive === "class" || p.primitive === "function" || p.primitive === "variable")) {
      if (!localByPath.has(p.source.path)) localByPath.set(p.source.path, new Map());
      localByPath.get(p.source.path)!.set(p.name, p.id);
    }
  }

  // Import bindings per file: local_binding -> target_id
  const importsByPath = new Map<string, Map<string, string>>();
  for (const p of prims) {
    if (p.primitive !== "module") continue;
    for (const e of p.edges_out) {
      if (e.kind !== "imports") continue;
      const lb = e.local_binding;
      if (lb) {
        if (!importsByPath.has(p.source.path)) importsByPath.set(p.source.path, new Map());
        importsByPath.get(p.source.path)!.set(lb, e.target);
      }
    }
  }

  // Dynamic-import-shim detection. The TS-ESM-in-CJS idiom looks like:
  //   const importESM = new Function('p', 'return import(p)') as ...
  // tsc would rewrite a real `import()` to `require()` in CJS mode, so authors
  // hide it behind a Function constructor. The body is a string literal, so we
  // can statically recognize the pattern and treat `importESM('mod')` calls as
  // dynamic imports of `'mod'` on the enclosing module — see
  // depgraph/tests/fixtures/wild/edges/dynamic_import_shim_ts.
  const SHIM_BODY_RE = /^\s*return\s+import\s*\(\s*([A-Za-z_$][\w$]*)\s*\)\s*;?\s*$/;
  const importShimsByPath = new Map<string, Set<string>>();
  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    for (const vs of sf.getVariableStatements()) {
      for (const decl of vs.getDeclarations()) {
        let init: any = decl.getInitializer();
        while (init && Node.isAsExpression(init)) init = init.getExpression();
        if (!init || !Node.isNewExpression(init)) continue;
        if (init.getExpression().getText() !== "Function") continue;
        const args = init.getArguments();
        if (args.length !== 2) continue;
        const literalText = (n: any): string | null =>
          Node.isStringLiteral(n) || Node.isNoSubstitutionTemplateLiteral(n)
            ? n.getLiteralText() : null;
        const paramName = literalText(args[0]);
        const body = literalText(args[1]);
        if (!paramName || body === null) continue;
        const m = body.match(SHIM_BODY_RE);
        if (!m || m[1] !== paramName) continue;
        if (!importShimsByPath.has(rel)) importShimsByPath.set(rel, new Set());
        importShimsByPath.get(rel)!.add(decl.getName());
      }
    }
  }

  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    const localNames = localByPath.get(rel) ?? new Map<string, string>();
    const imports = importsByPath.get(rel) ?? new Map<string, string>();
    const shims = importShimsByPath.get(rel);
    const localVars = varsByPath.get(rel);  // module-scope variables; undefined if file has none

    const resolveClass = (name: string): string | undefined => {
      const id = localNames.get(name) ?? imports.get(name);
      return id && allClassIds.has(id) ? id : undefined;
    };

    // Walk all function declarations (top-level + class methods)
    const allFns = [
      ...sf.getFunctions(),
      ...sf.getClasses().flatMap((c) => c.getMethods()),
      ...sf.getVariableStatements().flatMap((vs) =>
        vs.getDeclarations().filter((d) => {
          const init = d.getInitializer();
          return init && (Node.isArrowFunction(init) || Node.isFunctionExpression(init));
        })
      ),
    ];

    for (const fnNode of allFns as any[]) {
      const startLine = fnNode.getStartLineNumber();
      const fnPrim = fnByPathAndLine.get(`${rel}:${startLine}`);
      if (!fnPrim) continue;

      // var_types: local variable name -> class id
      const varTypes = new Map<string, string>();

      // Seed from parameter annotations via ts-morph Type API
      const params: any[] = fnNode.getParameters?.() ?? [];
      for (const param of params) {
        const typeNode = param.getTypeNode?.();
        if (!typeNode) continue;
        const typeName = typeNode.getText().split("<")[0].trim();
        const cid = resolveClass(typeName);
        if (cid) varTypes.set(param.getName(), cid);
      }

      // Visitor walk: getDescendants() would materialize every wrapper Node in
      // the function body up-front, holding all of them resident until the
      // outer for-loop finished — on large codebases that was a primary OOM
      // driver (#44). forEachDescendant streams nodes so each can be GC'd
      // after the callback returns. Document order is preserved.
      //
      // This single walk handles three edge kinds: calls/instantiates
      // (CallExpression, NewExpression), var-type seeding for method-call
      // receivers (VariableDeclaration), and reads/assigns against
      // module-scope variables (Identifier). They share the same fn-list
      // iteration so combining keeps wrapper-node churn proportional to one
      // pass, not three.
      fnNode.forEachDescendant?.((node: Node) => {
        // reads/assigns: module-scope variable access. Cheapest check first
        // (Identifier matches a huge fraction of nodes; only emit when the
        // file actually has module-scope vars).
        if (localVars && Node.isIdentifier(node)) {
          // Skip identifiers that occupy a "name slot" in their parent —
          // they don't read a binding, they're a syntactic name. Most
          // common false positive: `obj.x` where `x` matches a module-
          // scope var name would emit a spurious `reads` edge. Same for
          // property/method declarations, parameters, and destructuring
          // binding sites.
          const parent = node.getParent();
          if (parent) {
            if (Node.isPropertyAccessExpression(parent) && parent.getNameNode() === node) return;
            if (Node.isPropertyAssignment(parent) && parent.getNameNode() === node) return;
            if (Node.isShorthandPropertyAssignment(parent) && parent.getNameNode() === node) {
              // `{x}` — shorthand is a real read of `x`; fall through to
              // the emit path below.
            } else if (Node.isPropertyDeclaration(parent) && parent.getNameNode() === node) {
              return;
            } else if (Node.isPropertySignature(parent) && parent.getNameNode() === node) {
              return;
            } else if (Node.isMethodDeclaration(parent) && parent.getNameNode() === node) {
              return;
            } else if (Node.isMethodSignature(parent) && parent.getNameNode() === node) {
              return;
            } else if (Node.isParameterDeclaration(parent) && parent.getNameNode() === node) {
              return;
            } else if (Node.isBindingElement(parent) && parent.getNameNode() === node) {
              return;
            } else if (Node.isImportSpecifier(parent)) {
              return;
            } else if (Node.isExportSpecifier(parent)) {
              return;
            }
          }
          const idName = node.getText();
          const varId = localVars.get(idName);
          if (varId) {
            let isWrite = false;
            if (parent && Node.isBinaryExpression(parent)) {
              const op = parent.getOperatorToken().getText();
              if (op === "=" && parent.getLeft() === node) isWrite = true;
            }
            fnPrim.edges_out.push({
              target: varId,
              kind: isWrite ? "assigns" : "reads",
              via: isWrite ? "assignment_lhs" : "identifier_read",
              where: `${rel}:${node.getStartLineNumber()}`,
              confidence: "exact",
            });
          }
          // Identifier nodes can't simultaneously be the other kinds handled
          // below; fall through is harmless but skipping is cleaner.
          return;
        }

        // Pattern 1: const/let t: Service = new Service()
        if (Node.isVariableDeclaration(node)) {
          const typeNode = node.getTypeNode?.();
          if (typeNode) {
            const typeName = typeNode.getText().split("<")[0].trim();
            const cid = resolveClass(typeName);
            if (cid) varTypes.set(node.getName(), cid);
          }
          // Pattern 2: infer from initializer new Service()
          const init = node.getInitializer?.();
          if (init && Node.isNewExpression(init)) {
            const expr = init.getExpression().getText().split("<")[0].trim();
            const cid = resolveClass(expr);
            if (cid) varTypes.set(node.getName(), cid);
          }
        }

        // new Expression(...) → instantiates
        if (Node.isNewExpression(node)) {
          const expr = node.getExpression().getText().split("<")[0].trim();
          const targetId = localNames.get(expr) ?? imports.get(expr);
          if (targetId && allClassIds.has(targetId)) {
            fnPrim.edges_out.push({
              target: targetId, kind: "instantiates", via: "new_expression",
              where: `${rel}:${node.getStartLineNumber()}`, confidence: "exact",
            });
          }
        }

        // Call expression
        if (Node.isCallExpression(node)) {
          const callExpr = node.getExpression();

          if (Node.isIdentifier(callExpr)) {
            // bare name call: helper()
            const name = callExpr.getText();
            // Dynamic-import-shim: `importESM('mod')` is semantically `import('mod')`.
            // Emit on the enclosing module to match how static imports are attributed
            // (imports.source = module), and suppress the variable-targeted calls edge.
            if (shims?.has(name)) {
              const modPrim = modByPath.get(rel);
              const callArgs = (node as any).getArguments?.() ?? [];
              const first = callArgs[0];
              const specText = first && (Node.isStringLiteral(first) || Node.isNoSubstitutionTemplateLiteral(first))
                ? first.getLiteralText() : null;
              if (modPrim && specText) {
                // The shim idiom exists to import npm ESM packages from CJS; relative
                // shim calls don't occur in practice (real import() works fine for those).
                const target = specText.startsWith(".")
                  ? `external::unresolved::${specText}`
                  : `external::npm::${npmPkgFromSpec(specText)}`;  // #29
                modPrim.edges_out.push({
                  target, kind: "imports", via: "dynamic_import_shim",
                  where: `${rel}:${node.getStartLineNumber()}`,
                  confidence: specText.startsWith(".") ? "unresolved" : "fuzzy",
                });
              }
              return;
            }
            const targetId = localNames.get(name) ?? imports.get(name);
            // Emit `calls` when the target is a known function primitive OR an
            // external terminal (those skip target-kind validation in reconcile
            // and carry semantically-meaningful information — e.g. `useState()`
            // resolves through the imports map to `external::npm::react::useState`).
            // In-corpus non-function targets (variables holding callables, modules)
            // are intentionally dropped here; the reads pass picks them up.
            const isExternal = targetId?.startsWith("external::");
            if (targetId && (allFunctionIds.has(targetId) || isExternal)) {
              fnPrim.edges_out.push({
                target: targetId, kind: "calls", via: "function_call",
                where: `${rel}:${node.getStartLineNumber()}`, confidence: "exact",
              });
            }
          } else if (Node.isPropertyAccessExpression(callExpr)) {
            // receiver.method()
            const objExpr = callExpr.getExpression();
            const methodName = callExpr.getName();
            const recvName = objExpr.getText();
            const recvClassId = varTypes.get(recvName);
            if (recvClassId) {
              const methodId = methodsByClass.get(recvClassId)?.get(methodName);
              if (methodId) {
                fnPrim.edges_out.push({
                  target: methodId, kind: "calls", via: "method_call",
                  where: `${rel}:${node.getStartLineNumber()}`, confidence: "exact",
                });
              } else {
                // Canonical external-terminal shape is `external::<ecosystem>::<symbol>`
                // (3 segments). Use the bare class name as the symbol prefix —
                // embedding the full primitive id (`<repo>::<path>::<cls>`) would
                // produce a 5-segment string that fails the terminal format.
                const className = recvClassId.split("::").pop() ?? recvClassId;
                fnPrim.edges_out.push({
                  target: `external::unresolved::${className}.${methodName}`,
                  kind: "calls", via: "method_call",
                  where: `${rel}:${node.getStartLineNumber()}`, confidence: "unresolved",
                });
              }
            }
          }
        }
      });
    }
  }
}

// ---------------------------------------------------------------------------
// L2 edge resolution — Task 3.6: tests edges (assertion-scoped, TS)
// ---------------------------------------------------------------------------

// Framework primitive names that should never receive `tests` edges.
// Inlined as a constant until Phase 5 ClassificationConfig exists.
const TS_TEST_FRAMEWORK_PRIMITIVES = new Set([
  "describe", "it", "test", "expect", "beforeEach", "afterEach",
  "beforeAll", "afterAll", "vi", "vitest", "jest",
]);

function isTestPath(relPath: string): boolean {
  const last = relPath.split("/").pop() ?? "";
  return last.endsWith(".test.ts") || last.endsWith(".test.tsx")
    || last.endsWith(".spec.ts") || last.endsWith(".spec.tsx");
}

function attachTestsEdges(
  prims: Primitive[],
  sourceFiles: SourceFile[],
  repoKey: string,
  repoPath: string,
): void {
  // Build local symbol index per file: name -> id (non-method, owner-null)
  const localByPath = new Map<string, Map<string, string>>();
  for (const p of prims) {
    if (p.owner === null && (p.primitive === "class" || p.primitive === "function" || p.primitive === "variable")) {
      if (!localByPath.has(p.source.path)) localByPath.set(p.source.path, new Map());
      localByPath.get(p.source.path)!.set(p.name, p.id);
    }
  }

  // Build import bindings per file: local_binding -> target_id
  const importsByPath = new Map<string, Map<string, string>>();
  for (const p of prims) {
    if (p.primitive !== "module") continue;
    for (const e of p.edges_out) {
      if (e.kind !== "imports") continue;
      const lb = e.local_binding;
      if (lb) {
        if (!importsByPath.has(p.source.path)) importsByPath.set(p.source.path, new Map());
        importsByPath.get(p.source.path)!.set(lb, e.target);
      }
    }
  }

  // Index function primitives by path:line
  const fnByPathAndLine = new Map<string, Primitive>();
  for (const p of prims) {
    if (p.primitive === "function") {
      fnByPathAndLine.set(`${p.source.path}:${p.source.line}`, p);
    }
  }

  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    if (!isTestPath(rel)) continue;

    const localNames = localByPath.get(rel) ?? new Map<string, string>();
    const imports = importsByPath.get(rel) ?? new Map<string, string>();

    const allFns = [
      ...sf.getFunctions(),
      ...sf.getClasses().flatMap((c) => c.getMethods()),
    ];

    for (const fnNode of allFns as any[]) {
      const startLine = fnNode.getStartLineNumber();
      const fnPrim = fnByPathAndLine.get(`${rel}:${startLine}`);
      if (!fnPrim) continue;

      // Visitor walk over CallExpressions — see #44: getDescendants()
      // materialized every Node wrapper in the function body.
      fnNode.forEachDescendant?.((node: Node) => {
        if (!Node.isCallExpression(node)) return;

        // Check if this call is inside an expect(...) ancestor.
        // expect(add(1, 2)).toBe(3):
        //   - outer call: expect(...).toBe(3)  — PropertyAccessExpression callee
        //   - add(1, 2) is an argument to expect(...)
        // We want to emit tests edge for `add`, not for `expect` or `toBe`.
        //
        // Detection: walk up ancestors; if we reach a CallExpression whose
        // callee (or callee's object) is Identifier "expect", this node is
        // assertion-scoped.
        if (!isInsideExpect(node)) return;

        const callExpr = node.getExpression();
        let calleeName: string | null = null;
        if (Node.isIdentifier(callExpr)) {
          calleeName = callExpr.getText();
        } else if (Node.isPropertyAccessExpression(callExpr)) {
          calleeName = callExpr.getName();
        }
        if (!calleeName || TS_TEST_FRAMEWORK_PRIMITIVES.has(calleeName)) return;

        const targetId = localNames.get(calleeName) ?? imports.get(calleeName);
        if (targetId && !targetId.startsWith("external::")) {
          fnPrim.edges_out.push({
            target: targetId, kind: "tests", via: "asserted_call",
            where: `${rel}:${node.getStartLineNumber()}`, confidence: "exact",
          });
        }
      });
    }
  }
}

function isInsideExpect(node: Node): boolean {
  // Walk up the ancestor chain; return true if we encounter a CallExpression
  // whose direct callee is Identifier "expect".
  let cur: Node | undefined = node.getParent();
  while (cur !== undefined) {
    if (Node.isCallExpression(cur)) {
      const expr = cur.getExpression();
      // Direct call: expect(...)
      if (Node.isIdentifier(expr) && expr.getText() === "expect") return true;
      // Chained: expect(...).toBe(...) — callee is PropertyAccess on expect(...)
      if (Node.isPropertyAccessExpression(expr)) {
        const obj = expr.getExpression();
        if (Node.isCallExpression(obj)) {
          const innerExpr = obj.getExpression();
          if (Node.isIdentifier(innerExpr) && innerExpr.getText() === "expect") return true;
        }
      }
    }
    cur = cur.getParent();
  }
  return false;
}

// reads/assigns (#44): folded into attachCallAndVarAccessEdges so the per-fn
// descendant walk runs once for both edge categories instead of twice.

function splitCsv(s: string | undefined): string[] {
  if (!s) return [];
  return s.split(",").map((x) => x.trim()).filter(Boolean);
}

// ---------------------------------------------------------------------------
// route_call extraction
//
// Detect HTTP call sites (`fetch(...)`, `axios.<verb>(...)`) and emit
// `kind: "route_call"` primitives whose signature carries `{method,
// url_pattern}`. The signature's `url_pattern` is the join key against
// Python endpoints' `(method, path)` in reconcile / regen — interpolation
// in template literals is collapsed to the literal `<var>` token to match
// `_normalize_url_pattern` in `depgraph/extractors/reconcile.py`.
// ---------------------------------------------------------------------------

const _AXIOS_METHODS = new Set(["get", "post", "put", "patch", "delete", "head", "options"]);

function _urlPatternFromExpression(arg: Node): string | null {
  if (Node.isStringLiteral(arg) || Node.isNoSubstitutionTemplateLiteral(arg)) {
    return arg.getLiteralText();
  }
  if (Node.isTemplateExpression(arg)) {
    // `head${a}mid${b}tail` → "head<var>mid<var>tail"
    let out = arg.getHead().getLiteralText();
    for (const span of arg.getTemplateSpans()) {
      out += "<var>" + span.getLiteral().getLiteralText();
    }
    return out;
  }
  return null;
}

function _methodFromFetchInit(call: Node): string {
  // Default for `fetch(url)` is GET. `fetch(url, { method: "POST" })` reads
  // the method literal. Anything more dynamic falls back to GET — better a
  // best-guess match than dropping the call site silently.
  if (!Node.isCallExpression(call)) return "GET";
  const args = call.getArguments();
  if (args.length < 2) return "GET";
  const init = args[1];
  if (!Node.isObjectLiteralExpression(init)) return "GET";
  for (const prop of init.getProperties()) {
    if (!Node.isPropertyAssignment(prop)) continue;
    const name = prop.getName();
    if (name !== "method") continue;
    const value = prop.getInitializer();
    if (!value) continue;
    if (Node.isStringLiteral(value) || Node.isNoSubstitutionTemplateLiteral(value)) {
      return value.getLiteralText().toUpperCase();
    }
  }
  return "GET";
}

function _slugifyUrlForId(url: string): string {
  // Filename-safe slice of the URL pattern for the call site's id.
  return url.replace(/[^A-Za-z0-9_]/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
}

function _routeCallPrimitive(
  method: string, urlPattern: string, line: number, endLine: number,
  repoKey: string, relPath: string,
): Primitive {
  const id = `${repoKey}::${relPath}:${line}::${method}_${_slugifyUrlForId(urlPattern)}`;
  return {
    schema_version: 2,
    id,
    primitive: "function",
    name: `${method} ${urlPattern}`,
    owner: null,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line, end_line: endLine },
    signature: { method, url_pattern: urlPattern },
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable: false,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({ kind: "route_call", method, url: urlPattern }),
    kind: "route_call",
    extractor: EXTRACTOR_TAG,
  };
}

function extractRouteCalls(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  // Visitor-based walk: avoids materializing the full CallExpression descendant
  // array (which on large Next.js codebases pushed RSS past available RAM per
  // #44). Each visited Node is released to GC after the callback returns.
  const out: Primitive[] = [];
  sf.forEachDescendant((node) => {
    if (!Node.isCallExpression(node)) return;
    const call = node;
    const callee = call.getExpression();
    let method: string | null = null;
    let urlArg: Node | undefined;

    if (Node.isIdentifier(callee) && callee.getText() === "fetch") {
      method = _methodFromFetchInit(call);
      urlArg = call.getArguments()[0];
    } else if (Node.isPropertyAccessExpression(callee)) {
      const obj = callee.getExpression();
      const name = callee.getName();
      if (Node.isIdentifier(obj) && obj.getText() === "axios"
          && _AXIOS_METHODS.has(name)) {
        method = name.toUpperCase();
        urlArg = call.getArguments()[0];
      }
    }

    if (!method || !urlArg) return;
    const urlPattern = _urlPatternFromExpression(urlArg);
    if (!urlPattern) return;
    const line = call.getStartLineNumber();
    const endLine = call.getEndLineNumber();
    out.push(_routeCallPrimitive(method, urlPattern, line, endLine, repoKey, relPath));
  });
  return out;
}

function main() {
  const { values } = parseArgs({
    options: {
      "repo-key": { type: "string" },
      "repo-path": { type: "string" },
      "format": { type: "string", default: "ndjson" },
      "include-paths": { type: "string" },
      "exclude-paths": { type: "string" },
    },
  });
  const repoKey = values["repo-key"];
  const repoPath = values["repo-path"];
  if (!repoKey || !repoPath) {
    console.error("Usage: extract.ts --repo-key <key> --repo-path <path>");
    process.exit(1);
  }
  const includeRes = splitCsv(values["include-paths"]).map(compileGlob);
  const excludeRes = splitCsv(values["exclude-paths"]).map(compileGlob);

  // Initialize Project — try to find tsconfig.json in repo root for path alias support
  const tsconfigPath = `${repoPath}/tsconfig.json`;
  let project: Project;
  let hasTsconfig = false;
  try {
    statSync(tsconfigPath);
    hasTsconfig = true;
  } catch {
    hasTsconfig = false;
  }
  if (hasTsconfig) {
    project = new Project({ tsConfigFilePath: tsconfigPath, skipAddingFilesFromTsConfig: false });
    // Also add any source files not covered by tsconfig's include globs
    for (const f of listSourceFiles(repoPath)) {
      if (!project.getSourceFile(f)) project.addSourceFileAtPath(f);
    }
  } else {
    project = new Project({ skipAddingFilesFromTsConfig: true });
    for (const f of listSourceFiles(repoPath)) project.addSourceFileAtPath(f);
  }

  const sourceFiles = project.getSourceFiles().filter((sf) => {
    const fp = sf.getFilePath();
    if (fp.includes("/node_modules/") || fp.includes("/.git/")) return false;
    const rel = relative(repoPath, fp);
    if (includeRes.length && !matchesAny(rel, includeRes)) return false;
    if (excludeRes.length && matchesAny(rel, excludeRes)) return false;
    return true;
  });

  // Collect all primitives
  const allPrims: Primitive[] = [];
  for (const p of packagePrimitives(sourceFiles, repoKey, repoPath)) allPrims.push(p);
  for (const sf of sourceFiles) {
    const relPath = relative(repoPath, sf.getFilePath());
    allPrims.push(moduleFor(sf, repoKey, repoPath));
    for (const p of extractClasses(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractFunctions(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractVariables(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractObjectLiteralApiClients(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractRouteCalls(sf, repoKey, relPath)) allPrims.push(p);
  }

  // L2 edge resolution passes
  attachDefinesEdges(allPrims);
  attachInheritanceEdges(allPrims, sourceFiles, repoKey, repoPath);
  attachImportsEdges(allPrims, sourceFiles, repoKey, repoPath);
  // calls + instantiates + reads/assigns share one per-fn descendant walk (#44).
  attachCallAndVarAccessEdges(allPrims, sourceFiles, repoKey, repoPath);
  attachTestsEdges(allPrims, sourceFiles, repoKey, repoPath);

  for (const p of allPrims) emit(p);
}

// Only run main() when invoked as a script (`tsx extract.ts ...`). Skip
// when imported (e.g. by vitest tests that exercise the pure helpers).
const _invokedDirectly = (() => {
  try {
    return process.argv[1] === fileURLToPath(import.meta.url);
  } catch {
    return true;  // be permissive on environments lacking URL/import.meta
  }
})();
if (_invokedDirectly) main();
