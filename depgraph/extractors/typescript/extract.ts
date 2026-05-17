/**
 * Layered-substrate TS extractor — emits primitives only.
 * Schema v2; see docs/superpowers/specs/2026-05-15-layered-substrate-design.md.
 */
import { Project, SourceFile, SyntaxKind, Node } from "ts-morph";
import { parseArgs } from "node:util";
import { readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
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
  kind: null;
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
      const targetRel2 = targetSf2 ? relative(repoPath, targetSf2.getFilePath()) : null;
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
      const targetRel = targetSf ? relative(repoPath, targetSf.getFilePath()) : null;
      const targetSyms = targetRel ? (symByPath.get(targetRel) ?? new Map()) : new Map();
      const targetReexports = targetRel ? (reexportMap.get(targetRel) ?? new Map()) : new Map();

      const defaultImport = imp.getDefaultImport();
      if (defaultImport) {
        const localBinding = defaultImport.getText();
        const defaultId = targetRel ? defaultExportMap.get(targetRel) : undefined;
        const target = defaultId
          ? defaultId
          : targetRel
            ? `${repoKey}::${targetRel}::default`
            : `external::npm::unknown::default`;
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
        const target = targetRel
          ? `${repoKey}::${targetRel}`
          : `external::npm::unknown`;
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
              target = `${repoKey}::${targetRel}`;
              confidence = "exact";
            }
          }
        } else {
          // Unresolved external
          const specText = imp.getModuleSpecifierValue();
          const pkgName = specText.startsWith(".")
            ? "local"
            : specText.split("/")[0].replace(/^@/, "");
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
      const targetRel2 = targetSf2 ? relative(repoPath, targetSf2.getFilePath()) : null;
      const targetSyms2 = targetRel2 ? (symByPath.get(targetRel2) ?? new Map()) : new Map();
      const targetReexports2 = targetRel2 ? (reexportMap.get(targetRel2) ?? new Map()) : new Map();

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
              : `external::npm::unknown::${exportedName}`;
        modPrim.edges_out.push({
          target, kind: "imports", via: "re_export",
          where: `${rel}:${exp.getStartLineNumber()}`,
          confidence: "fuzzy", local_binding: localBinding,
        });
      }
    }
  }
}

// ---------------------------------------------------------------------------
// L2 edge resolution — Task 3.4: calls + instantiates (intra-fn type binding)
// ---------------------------------------------------------------------------

function attachCallEdges(
  prims: Primitive[],
  sourceFiles: SourceFile[],
  repoKey: string,
  repoPath: string,
): void {
  const classesByPath = new Map<string, Map<string, Primitive>>();
  const methodsByClass = new Map<string, Map<string, string>>(); // classId -> {methodName -> fnId}
  const fnByPathAndLine = new Map<string, Primitive>(); // "path:line" -> prim
  const modByPath = new Map<string, Primitive>();
  for (const p of prims) {
    if (p.primitive === "module") modByPath.set(p.source.path, p);
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

  // All class ids as a set for quick lookup
  const allClassIds = new Set(prims.filter((p) => p.primitive === "class").map((p) => p.id));

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

      // Walk descendants in document order
      const descendants = fnNode.getDescendants?.() ?? [];
      for (const node of descendants) {
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
                  : `external::npm::${specText.split("/")[0].replace(/^@/, "")}`;
                modPrim.edges_out.push({
                  target, kind: "imports", via: "dynamic_import_shim",
                  where: `${rel}:${node.getStartLineNumber()}`,
                  confidence: specText.startsWith(".") ? "unresolved" : "fuzzy",
                });
              }
              continue;
            }
            const targetId = localNames.get(name) ?? imports.get(name);
            if (targetId && !allClassIds.has(targetId)) {
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
                fnPrim.edges_out.push({
                  target: `external::unresolved::${recvClassId}.${methodName}`,
                  kind: "calls", via: "method_call",
                  where: `${rel}:${node.getStartLineNumber()}`, confidence: "unresolved",
                });
              }
            }
          }
        }
      }
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

      // Walk descendants looking for CallExpressions
      const descendants = fnNode.getDescendants?.() ?? [];
      for (const node of descendants) {
        if (!Node.isCallExpression(node)) continue;

        // Check if this call is inside an expect(...) ancestor.
        // expect(add(1, 2)).toBe(3):
        //   - outer call: expect(...).toBe(3)  — PropertyAccessExpression callee
        //   - add(1, 2) is an argument to expect(...)
        // We want to emit tests edge for `add`, not for `expect` or `toBe`.
        //
        // Detection: walk up ancestors; if we reach a CallExpression whose
        // callee (or callee's object) is Identifier "expect", this node is
        // assertion-scoped.
        if (!isInsideExpect(node)) continue;

        const callExpr = node.getExpression();
        let calleeName: string | null = null;
        if (Node.isIdentifier(callExpr)) {
          calleeName = callExpr.getText();
        } else if (Node.isPropertyAccessExpression(callExpr)) {
          calleeName = callExpr.getName();
        }
        if (!calleeName || TS_TEST_FRAMEWORK_PRIMITIVES.has(calleeName)) continue;

        const targetId = localNames.get(calleeName) ?? imports.get(calleeName);
        if (targetId && !targetId.startsWith("external::")) {
          fnPrim.edges_out.push({
            target: targetId, kind: "tests", via: "asserted_call",
            where: `${rel}:${node.getStartLineNumber()}`, confidence: "exact",
          });
        }
      }
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

// ---------------------------------------------------------------------------
// L2 edge resolution — Task 3.5: reads / assigns (TS)
// ---------------------------------------------------------------------------

function attachVarAccessEdges(
  prims: Primitive[],
  sourceFiles: SourceFile[],
  repoKey: string,
  repoPath: string,
): void {
  // Index module-scope variable primitives per file: name -> id
  const varsByPath = new Map<string, Map<string, string>>();
  for (const p of prims) {
    if (p.primitive === "variable" && p.owner === null) {
      if (!varsByPath.has(p.source.path)) varsByPath.set(p.source.path, new Map());
      varsByPath.get(p.source.path)!.set(p.name, p.id);
    }
  }

  // Index function primitives by path:line for fast lookup
  const fnByPathAndLine = new Map<string, Primitive>();
  for (const p of prims) {
    if (p.primitive === "function") {
      fnByPathAndLine.set(`${p.source.path}:${p.source.line}`, p);
    }
  }

  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    const localVars = varsByPath.get(rel);
    if (!localVars || localVars.size === 0) continue;

    // Walk all function nodes
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

      // Walk all Identifier descendants
      const descendants = fnNode.getDescendants?.() ?? [];
      for (const node of descendants) {
        if (!Node.isIdentifier(node)) continue;
        const name = node.getText();
        const varId = localVars.get(name);
        if (!varId) continue;

        // Determine if this is a read or write
        const parent = node.getParent();
        let isWrite = false;
        if (parent && Node.isBinaryExpression(parent)) {
          // Left-hand side of assignment: x = 1
          const op = parent.getOperatorToken().getText();
          if (op === "=" && parent.getLeft() === node) {
            isWrite = true;
          }
        }

        fnPrim.edges_out.push({
          target: varId,
          kind: isWrite ? "assigns" : "reads",
          via: isWrite ? "assignment_lhs" : "identifier_read",
          where: `${rel}:${node.getStartLineNumber()}`,
          confidence: "exact",
        });
      }
    }
  }
}

function splitCsv(s: string | undefined): string[] {
  if (!s) return [];
  return s.split(",").map((x) => x.trim()).filter(Boolean);
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
  }

  // L2 edge resolution passes
  attachDefinesEdges(allPrims);
  attachInheritanceEdges(allPrims, sourceFiles, repoKey, repoPath);
  attachImportsEdges(allPrims, sourceFiles, repoKey, repoPath);
  attachCallEdges(allPrims, sourceFiles, repoKey, repoPath);
  attachVarAccessEdges(allPrims, sourceFiles, repoKey, repoPath);
  attachTestsEdges(allPrims, sourceFiles, repoKey, repoPath);

  for (const p of allPrims) emit(p);
}

main();
