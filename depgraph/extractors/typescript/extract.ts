/**
 * Layered-substrate TS extractor — emits primitives only.
 * Schema v2; see docs/superpowers/specs/2026-05-15-layered-substrate-design.md.
 *
 * ## Streaming architecture (issue #47)
 *
 * ts-morph's `Project` keeps every `SourceFile`'s AST resident from
 * `addSourceFileAtPath` through the last consumer. On large corpora that
 * resident set dominates RSS and produces the architectural OOM ceiling.
 *
 * The L1 pass now extracts both (a) primitives and (b) a compact
 * `PerFileMetadata` record that captures everything L2 needs (imports,
 * re-exports, default-export markers, class extends/implements names,
 * per-function call/identifier/var-decl event streams, dynamic-import
 * shims). After each file finishes L1, `sf.forget()` releases its AST.
 *
 * L2 passes (`attachInheritanceEdges`, `attachImportsEdges`,
 * `attachCallAndVarAccessEdges`, `attachTestsEdges`) consume the
 * primitive list and per-file metadata maps only — no AST access. The
 * symbol-resolution maps they build (`symByPath`, `importsByPath`,
 * `namedReexports`, `reexportMap`, `defaultExportMap`, `classesByPath`,
 * `methodsByClass`) are all derived from the metadata.
 *
 * tsconfig path-alias resolution still rides on ts-morph's `Project` —
 * we resolve `imp.getModuleSpecifierSourceFile()` during L1 and store
 * the result as the metadata's `resolved_rel`, so L2 doesn't need the
 * `Project` instance at all.
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

// ---------------------------------------------------------------------------
// Per-file metadata (issue #47)
//
// Captures everything L2 reads from each source file's AST. Populated during
// L1 (while the SourceFile is still loaded), then the SourceFile is forgotten
// so its AST can be GC'd before the next L1 iteration.
// ---------------------------------------------------------------------------

interface NamedImportSpec {
  name: string;          // exported name in the target module
  local_binding: string; // local name (may equal `name` if no alias)
}
interface NamedExportSpec {
  name: string;          // exported name in the target module (or the same module for `export { x }`)
  consumer_name: string; // name the consumer sees (alias if `as`, else `name`)
}
interface ImportDeclMeta {
  spec_text: string;         // raw module specifier text
  resolved_rel: string | null; // resolved in-corpus rel path (null = external / unresolved / node_modules)
  line: number;
  default_import: string | null;   // local binding name of `import X from ...`
  namespace_import: string | null; // local binding name of `import * as X from ...`
  named: NamedImportSpec[];
}
interface ExportDeclMeta {
  // `export ... from "..."` re-export declarations only (those without a
  // module specifier never reach this list).
  spec_text: string;
  resolved_rel: string | null;
  line: number;
  named: NamedExportSpec[];
  has_namespace_export: boolean; // `export * as ns from "..."`
  is_wildcard: boolean;          // `export * from "..."` (no namespace alias, no named exports)
}
interface DynamicImportMeta {
  spec_text: string | null; // null when first arg isn't a string literal
  line: number;
}
interface ClassMeta {
  name: string;
  // `extends Foo<Bar>` → "Foo" (we drop generic args to match the old
  // `getText().split("<")[0].trim()` resolver behavior).
  extends_name: string | null;
  extends_line: number | null;
  implements: { name: string; line: number }[];
}
interface ParamMeta {
  name: string;
  // textual type annotation, generics stripped (split-by-`<`, then trim).
  type_name: string | null;
}
// Per-function event stream. Mirrors the visitor-walk inside the old
// attachCallAndVarAccessEdges + attachTestsEdges; recorded in document order
// so semantic replays (e.g. is_inside_expect ancestor checks) preserve
// behavior. Each event corresponds to a single AST node we'd previously
// inspect; the L2 passes treat the list as the function body.
type FnEvent =
  | {
      kind: "identifier";
      name: string;
      line: number;
      is_assignment_lhs: boolean;
      // The ancestor-chain check `isInsideExpect`. Captured at L1 because L2
      // can't walk the AST. We only flag identifiers used as a call callee
      // — the tests pass restricts to call expressions, so this only matters
      // when this identifier is also a CallExpression event below. For
      // module-scope reads/assigns we don't need this flag.
      inside_expect: boolean;
    }
  | {
      kind: "var_decl";
      name: string;
      type_name: string | null;          // `const x: Foo = ...` → "Foo"
      new_expr_class_name: string | null; // `const x = new Foo()` → "Foo"
    }
  | {
      kind: "new";
      class_name: string;
      line: number;
    }
  | {
      kind: "call_bare";
      callee_name: string;
      line: number;
      inside_expect: boolean;
      // Argument summary for the dynamic-import-shim detector + tests pass.
      // We capture the first arg's literal value if it's a string literal so
      // L2 can recover `importESM('mod')` semantics without re-reading args.
      first_arg_literal: string | null;
    }
  | {
      kind: "call_method";
      receiver_text: string;
      method_name: string;
      line: number;
      inside_expect: boolean;
    }
  | {
      kind: "call_dynamic_import";
      // `await import("./rel")` or `await import("pkg")` — already resolved
      // to a rel path during L1 if relative+in-corpus, else null.
      spec_text: string | null;
      resolved_rel: string | null;
      line: number;
    };
interface FnMeta {
  // `path:start_line` matches the key used by L2 to look up the function's
  // primitive id (`fnByPathAndLine` in the old code).
  start_line: number;
  parameters: ParamMeta[];
  events: FnEvent[];
}
interface ImportShimMeta {
  // Module-scope const whose initializer is `new Function('p', 'return import(p)')`.
  // Recorded so L2 can recognize `importESM('mod')` calls as dynamic imports
  // attributed to the enclosing module.
  binding_name: string;
}
interface PerFileMetadata {
  rel_path: string;
  // Class metadata used by attachInheritanceEdges + attachCallAndVarAccessEdges'
  // class index. Stored in declaration order.
  classes: ClassMeta[];
  imports: ImportDeclMeta[];
  exports: ExportDeclMeta[];     // `export ... from "..."` re-exports
  dynamic_imports: DynamicImportMeta[]; // top-level dynamic imports (NOT inside fns; those ride on FnEvent.call_dynamic_import)
  // `export default X` where X is an Identifier resolving in the local scope.
  // L1 stores the local identifier text; L2 resolves it against symByPath.
  default_export_identifier: string | null;
  // Top-level `export default class X {}` / `export default function X(){}`:
  // we record the bound name so L2 can look it up in symByPath.
  default_export_class_or_fn_name: string | null;
  // Function metadata. Indexed by `start_line`.
  functions: FnMeta[];
  // Dynamic-import-shim bindings (module-scope only).
  import_shims: ImportShimMeta[];
}

const EXTRACTOR_TAG = "depgraph/extractors/typescript/extract.ts@2026-05-22c";
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

// Pre-pass: walk every SourceFile once for directory layout. Kept separate
// from L1 because L1 forgets SourceFiles in-line — and packagePrimitives
// only needs `sf.getFilePath()`, which the wrapper still exposes even after
// forget, but we want to drive the per-rel-path set off something stable.
function packagePrimitivesFromRelPaths(relPaths: string[], repoKey: string): Primitive[] {
  const dirs = new Set<string>();
  for (const rel of relPaths) {
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

// Synthetic `<file>::default` primitive for every default-exporting module.
//
// Without this, `import X from './mod'` produces an import edge whose
// target is `<mod>::default` — and if `<mod>` has `export default <expr>`
// (e.g. `export default defineConfig(...)`), no primitive exists at that
// id and the edge is orphaned (#85).
//
// We emit a synthetic `variable` primitive at `<file>::default` for ALL
// default-export forms — both expressions (ExportAssignment) and
// default-keyword declarations (`export default class X {}` /
// `export default function f() {}`). This makes `<file>::default` always
// a real primitive when the file has a default export, regardless of the
// resolver's choice (defaultExportMap may rewrite the edge to the named
// primitive, but the synthetic shadow at `<file>::default` is always
// resolvable too).
//
// The value_text is the truncated source text of the default-export
// statement, capped at SIGNATURE_VALUE_CAP to keep structural_hash and
// node payloads bounded.
const SIGNATURE_VALUE_CAP = 200;

function truncatedSignature(text: string): string {
  const collapsed = text.replace(/\s+/g, " ").trim();
  if (collapsed.length <= SIGNATURE_VALUE_CAP) return collapsed;
  return collapsed.slice(0, SIGNATURE_VALUE_CAP) + "…";
}

function extractDefaultExport(sf: SourceFile, repoKey: string, relPath: string): Primitive[] {
  // Detect the default-export site, if any. Three shapes:
  //   1. ExportAssignment (`export default <expr>`) — not export-equals.
  //   2. ClassDeclaration with `default` modifier (`export default class X {}`).
  //   3. FunctionDeclaration with `default` modifier
  //      (`export default function f() {}` or `export default function () {}`).
  let node: { getStartLineNumber(): number; getEndLineNumber(): number; getText(): string } | null = null;

  for (const ea of sf.getExportAssignments()) {
    if (ea.isExportEquals()) continue;
    node = ea;
    break;
  }
  if (!node) {
    for (const cls of sf.getClasses()) {
      if (cls.hasDefaultKeyword()) { node = cls; break; }
    }
  }
  if (!node) {
    for (const fn of sf.getFunctions()) {
      if (fn.hasDefaultKeyword()) { node = fn; break; }
    }
  }
  if (!node) return [];

  const valueText = truncatedSignature(node.getText());
  const id = canonicalId(repoKey, relPath, "default");
  return [{
    schema_version: 2, id,
    primitive: "variable", name: "default", owner: null,
    source: { repo: repoKey, path: relPath, language: "typescript",
              line: node.getStartLineNumber(), end_line: node.getEndLineNumber() },
    signature: { type_annotation: null, value_text: valueText },
    attributes: { abstract: false, generated: false, external: false,
                  template_parameters: [], macro: false, mutable: false,
                  instantiable: false, inheritable: false },
    edges_out: [],
    structural_hash: structuralHash({
      primitive: "variable", name: "default",
      signature: { type_annotation: null, value_text: valueText },
      body_text: valueText,
    }),
    kind: null,
    extractor: EXTRACTOR_TAG,
  }];
}

// ---------------------------------------------------------------------------
// L1 metadata extraction (issue #47)
//
// Single per-file pass that produces a PerFileMetadata while the SourceFile
// is still loaded. Called from main() once per file; the SourceFile is
// forgotten after this returns so the AST can be GC'd before the next
// iteration. All data L2 needs must be captured here.
// ---------------------------------------------------------------------------

// Strip generics + whitespace from a type-name text. Matches the old
// `getText().split("<")[0].trim()` recipe used by the call/var-access pass.
function stripGenerics(text: string): string {
  return text.split("<")[0].trim();
}

// `await import("./rel")` shim-detection regex (the body of a Function-constructor
// shim must match `return import(p);` exactly to be recognized).
const SHIM_BODY_RE = /^\s*return\s+import\s*\(\s*([A-Za-z_$][\w$]*)\s*\)\s*;?\s*$/;

// Pre-pass: resolve every import-decl and re-export-decl's module specifier
// to its in-corpus rel-path. ts-morph's `getModuleSpecifierSourceFile()`
// requires that the target SourceFile is still loaded in the Project — once
// any file is forgotten, every consumer's resolution against that target
// stops working. Run this for all files first, then forget files in the
// heavy per-file loop afterwards.
//
// Returns:
//   resolvedImports.get(rel)[importDeclIndex]  → resolved_rel | null
//   resolvedExports.get(rel)[exportDeclIndex]  → resolved_rel | null
//
// Indices are positional — the L1 metadata extractor walks the same arrays
// in the same order to align them.
interface ResolvedSpecMap {
  imports: (string | null)[];
  exports: (string | null)[];
}
function buildResolvedSpecMap(
  sourceFiles: SourceFile[],
  repoPath: string,
): Map<string, ResolvedSpecMap> {
  const out = new Map<string, ResolvedSpecMap>();
  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    const importResolutions: (string | null)[] = [];
    for (const imp of sf.getImportDeclarations()) {
      const targetSf = imp.getModuleSpecifierSourceFile();
      const resolvedRaw = targetSf ? relative(repoPath, targetSf.getFilePath()) : null;
      importResolutions.push(inNodeModules(resolvedRaw) ? null : resolvedRaw);
    }
    const exportResolutions: (string | null)[] = [];
    for (const exp of sf.getExportDeclarations()) {
      if (!exp.hasModuleSpecifier()) {
        // Keep array length aligned with getExportDeclarations() — we'll
        // skip non-spec exports inside the metadata extractor too, but the
        // positional alignment only matters for spec-bearing ones; we still
        // record null here for safety.
        exportResolutions.push(null);
        continue;
      }
      const targetSf2 = exp.getModuleSpecifierSourceFile();
      const resolvedRaw = targetSf2 ? relative(repoPath, targetSf2.getFilePath()) : null;
      exportResolutions.push(inNodeModules(resolvedRaw) ? null : resolvedRaw);
    }
    out.set(rel, { imports: importResolutions, exports: exportResolutions });
  }
  return out;
}

function extractPerFileMetadata(
  sf: SourceFile,
  repoPath: string,
  relPath: string,
  resolvedSpecs: ResolvedSpecMap,
): PerFileMetadata {
  const meta: PerFileMetadata = {
    rel_path: relPath,
    classes: [],
    imports: [],
    exports: [],
    dynamic_imports: [],
    default_export_identifier: null,
    default_export_class_or_fn_name: null,
    functions: [],
    import_shims: [],
  };

  // Class metadata (extends/implements). Type aliases / interfaces / enums
  // don't have extends/implements clauses we care about.
  for (const cls of sf.getClasses()) {
    const cm: ClassMeta = {
      name: cls.getName() ?? "<anonymous>",
      extends_name: null,
      extends_line: null,
      implements: [],
    };
    const ex = cls.getExtends();
    if (ex) {
      cm.extends_name = ex.getExpression().getText();
      cm.extends_line = ex.getStartLineNumber();
    }
    for (const impl of cls.getImplements()) {
      cm.implements.push({
        name: impl.getExpression().getText(),
        line: impl.getStartLineNumber(),
      });
    }
    meta.classes.push(cm);
  }

  // Imports. The cross-file resolved rel-paths come from `resolvedSpecs`,
  // built in a pre-pass before any sf.forget() — ts-morph's resolution
  // breaks for forgotten target files, so we cannot call
  // `getModuleSpecifierSourceFile()` here. Positional index alignment with
  // `sf.getImportDeclarations()` is required.
  const importDecls = sf.getImportDeclarations();
  for (let i = 0; i < importDecls.length; i++) {
    const imp = importDecls[i];
    const specText = imp.getModuleSpecifierValue();
    const resolvedRel = resolvedSpecs.imports[i] ?? null;
    const named: NamedImportSpec[] = [];
    for (const spec of imp.getNamedImports()) {
      const aliasNode = spec.getAliasNode();
      named.push({
        name: spec.getName(),
        local_binding: aliasNode ? aliasNode.getText() : spec.getName(),
      });
    }
    meta.imports.push({
      spec_text: specText,
      resolved_rel: resolvedRel,
      line: imp.getStartLineNumber(),
      default_import: imp.getDefaultImport()?.getText() ?? null,
      namespace_import: imp.getNamespaceImport()?.getText() ?? null,
      named,
    });
  }

  // Re-exports: `export ... from "..."`. We skip export declarations with no
  // module specifier — those don't participate in the import-edge resolver.
  const exportDecls = sf.getExportDeclarations();
  for (let i = 0; i < exportDecls.length; i++) {
    const exp = exportDecls[i];
    if (!exp.hasModuleSpecifier()) continue;
    const specText = exp.getModuleSpecifierValue() ?? "";
    const resolvedRel = resolvedSpecs.exports[i] ?? null;
    const named = exp.getNamedExports();
    const namedExports: NamedExportSpec[] = [];
    for (const spec of named) {
      const exportedName = spec.getName();
      const aliasNode = spec.getAliasNode();
      namedExports.push({
        name: exportedName,
        consumer_name: aliasNode ? aliasNode.getText() : exportedName,
      });
    }
    const hasNamespace = !!exp.getNamespaceExport();
    meta.exports.push({
      spec_text: specText,
      resolved_rel: resolvedRel,
      line: exp.getStartLineNumber(),
      named: namedExports,
      has_namespace_export: hasNamespace,
      is_wildcard: namedExports.length === 0 && !hasNamespace,
    });
  }

  // Default-export identifier markers. Two shapes:
  //   `export default someIdent;` → record `someIdent` (L2 resolves)
  //   `export default class X {}`  → record `X` so L2 can chase via symByPath
  for (const ea of sf.getExportAssignments()) {
    if (ea.isExportEquals()) continue;
    const expr = ea.getExpression();
    if (Node.isIdentifier(expr)) {
      meta.default_export_identifier = expr.getText();
      break;
    }
  }
  if (meta.default_export_identifier === null) {
    for (const cls of sf.getClasses()) {
      if (cls.hasDefaultKeyword()) {
        const name = cls.getName();
        if (name) { meta.default_export_class_or_fn_name = name; break; }
      }
    }
  }
  if (meta.default_export_identifier === null && meta.default_export_class_or_fn_name === null) {
    for (const fn of sf.getFunctions()) {
      if (fn.hasDefaultKeyword()) {
        const name = fn.getName();
        if (name) { meta.default_export_class_or_fn_name = name; break; }
      }
    }
  }

  // Module-scope dynamic-import-shim detection. Pattern:
  //   const importESM = new Function('p', 'return import(p)') as ...
  // We record the binding so L2 can treat `importESM('mod')` calls as
  // dynamic imports of `'mod'`.
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
      meta.import_shims.push({ binding_name: decl.getName() });
    }
  }

  // Top-level dynamic imports (visitor walk; module-scope only). We use a
  // single sweep — the per-function event streams below capture nested ones.
  // The old code attributed *all* dynamic imports to the enclosing module,
  // not the enclosing function, so we mirror that here.
  sf.forEachDescendant((node) => {
    if (!Node.isCallExpression(node)) return;
    if (node.getExpression().getKind() !== SyntaxKind.ImportKeyword) return;
    const args = node.getArguments();
    if (args.length === 0) return;
    const first = args[0];
    if (!Node.isStringLiteral(first) && !Node.isNoSubstitutionTemplateLiteral(first)) {
      // Non-literal spec — record null so L2 still ticks the unresolved
      // bucket if it ever wants to (today's behavior: silently skip).
      meta.dynamic_imports.push({
        spec_text: null,
        line: node.getStartLineNumber(),
      });
      return;
    }
    meta.dynamic_imports.push({
      spec_text: (first as any).getLiteralText(),
      line: node.getStartLineNumber(),
    });
  });

  // Per-function event extraction. Mirrors the AST shape consumed by the
  // old attachCallAndVarAccessEdges + attachTestsEdges visitor walks.
  // The set of "functions" matches the function-primitive emitter (top-level
  // fns + class methods + arrow/expr-bound variable decls), so the `start_line`
  // index later matches `fnByPathAndLine` entries.
  //
  // We walk each fn's forEachDescendant once; the event stream contains
  // every Identifier/VarDecl/NewExpression/CallExpression we care about,
  // in document order.
  const fnNodes: any[] = [
    ...sf.getFunctions(),
    ...sf.getClasses().flatMap((c) => c.getMethods()),
    ...sf.getVariableStatements().flatMap((vs) =>
      vs.getDeclarations().filter((d) => {
        const init = d.getInitializer();
        return init && (Node.isArrowFunction(init) || Node.isFunctionExpression(init));
      })
    ),
  ];
  for (const fnNode of fnNodes) {
    const startLine: number = fnNode.getStartLineNumber();
    const params: any[] = fnNode.getParameters?.() ?? [];
    const fm: FnMeta = {
      start_line: startLine,
      parameters: params.map((p: any) => ({
        name: p.getName(),
        type_name: p.getTypeNode?.()
          ? stripGenerics(p.getTypeNode().getText())
          : null,
      })),
      events: [],
    };
    // Issue #82: per-fn scope-bindings map for identifier shadowing detection.
    // Built lazily — cheap on small fns, irrelevant on fns with no identifiers.
    const scopeBindings = collectScopeBindings(fnNode);
    fnNode.forEachDescendant?.((node: Node) => {
      // Identifiers (read/write detection). Skip identifiers that occupy
      // a syntactic "name slot" (property keys, parameter binding sites,
      // import/export specifiers, etc.), and skip those shadowed by a
      // local binding in any enclosing scope.
      if (Node.isIdentifier(node)) {
        if (identifierIsNameSlot(node)) return;
        const idName = node.getText();
        // Shorthand property assignment `{x}` IS a real read; the
        // name-slot filter intentionally lets it through. The
        // scope-shadowing check still applies.
        if (isLocallyBound(node, fnNode as Node, idName, scopeBindings)) return;
        const parent = node.getParent();
        let isWrite = false;
        if (parent && Node.isBinaryExpression(parent)) {
          const op = parent.getOperatorToken().getText();
          if (op === "=" && parent.getLeft() === node) isWrite = true;
        }
        fm.events.push({
          kind: "identifier",
          name: idName,
          line: node.getStartLineNumber(),
          is_assignment_lhs: isWrite,
          inside_expect: false, // not consulted for identifier events
        });
        return;
      }
      // VariableDeclaration (for var-type seeding in the call resolver).
      if (Node.isVariableDeclaration(node)) {
        const typeNode = node.getTypeNode?.();
        const typeName = typeNode ? stripGenerics(typeNode.getText()) : null;
        const init = node.getInitializer?.();
        let newClassName: string | null = null;
        if (init && Node.isNewExpression(init)) {
          newClassName = stripGenerics(init.getExpression().getText());
        }
        fm.events.push({
          kind: "var_decl",
          name: node.getName(),
          type_name: typeName,
          new_expr_class_name: newClassName,
        });
        // Don't return — VariableDeclaration won't match the call/new kinds
        // below, but we fall through to be safe.
      }
      // NewExpression → instantiates candidate
      if (Node.isNewExpression(node)) {
        fm.events.push({
          kind: "new",
          class_name: stripGenerics(node.getExpression().getText()),
          line: node.getStartLineNumber(),
        });
      }
      // CallExpression → calls / dynamic-import / tests
      if (Node.isCallExpression(node)) {
        const callExpr = node.getExpression();
        const line = node.getStartLineNumber();
        const insideExpect = isInsideExpectAst(node);
        // Dynamic import: `import("...")` — the import keyword is the callee.
        if (callExpr.getKind() === SyntaxKind.ImportKeyword) {
          const args = node.getArguments();
          let spec: string | null = null;
          if (args.length > 0) {
            const first = args[0];
            if (Node.isStringLiteral(first) || Node.isNoSubstitutionTemplateLiteral(first)) {
              spec = (first as any).getLiteralText();
            }
          }
          fm.events.push({
            kind: "call_dynamic_import",
            spec_text: spec,
            resolved_rel: null, // resolved by L2 against modByPath
            line,
          });
          return;
        }
        if (Node.isIdentifier(callExpr)) {
          // Bare-name call.
          const args = node.getArguments();
          let firstArgLit: string | null = null;
          if (args.length > 0) {
            const a0 = args[0];
            if (Node.isStringLiteral(a0) || Node.isNoSubstitutionTemplateLiteral(a0)) {
              firstArgLit = (a0 as any).getLiteralText();
            }
          }
          fm.events.push({
            kind: "call_bare",
            callee_name: callExpr.getText(),
            line,
            inside_expect: insideExpect,
            first_arg_literal: firstArgLit,
          });
        } else if (Node.isPropertyAccessExpression(callExpr)) {
          fm.events.push({
            kind: "call_method",
            receiver_text: callExpr.getExpression().getText(),
            method_name: callExpr.getName(),
            line,
            inside_expect: insideExpect,
          });
        }
      }
    });
    meta.functions.push(fm);
  }

  return meta;
}

// Scope-tracking helpers (issue #82 — see baseline extract.ts). Used to
// suppress reads/assigns edges when an identifier resolves to a local
// binding (parameter, let/const/var, destructure, catch var) in any
// enclosing scope of the function, rather than to the module-scope var of
// the same name.
function isScopeNode(n: Node): boolean {
  return (
    Node.isFunctionDeclaration(n) ||
    Node.isFunctionExpression(n) ||
    Node.isArrowFunction(n) ||
    Node.isMethodDeclaration(n) ||
    Node.isConstructorDeclaration(n) ||
    Node.isGetAccessorDeclaration(n) ||
    Node.isSetAccessorDeclaration(n) ||
    Node.isBlock(n) ||
    Node.isForStatement(n) ||
    Node.isForInStatement(n) ||
    Node.isForOfStatement(n) ||
    Node.isCatchClause(n)
  );
}

function collectScopeBindings(fnNode: Node): Map<Node, Set<string>> {
  const scopeBindings = new Map<Node, Set<string>>();
  const enclosingScope = (n: Node): Node | undefined => {
    let cur: Node | undefined = n.getParent();
    while (cur) {
      if (cur === fnNode || isScopeNode(cur)) return cur;
      cur = cur.getParent();
    }
    return undefined;
  };
  const addBinding = (scope: Node, name: string): void => {
    let s = scopeBindings.get(scope);
    if (!s) { s = new Set(); scopeBindings.set(scope, s); }
    s.add(name);
  };
  scopeBindings.set(fnNode, new Set());
  fnNode.forEachDescendant?.((node: Node) => {
    if (Node.isParameterDeclaration(node)) {
      const nameNode = node.getNameNode();
      if (Node.isIdentifier(nameNode)) {
        const scope = enclosingScope(node);
        if (scope) addBinding(scope, nameNode.getText());
      }
      return;
    }
    if (Node.isVariableDeclaration(node)) {
      const nameNode = node.getNameNode();
      if (Node.isIdentifier(nameNode)) {
        const scope = enclosingScope(node);
        if (scope) addBinding(scope, nameNode.getText());
      }
      return;
    }
    if (Node.isBindingElement(node)) {
      const nameNode = node.getNameNode();
      if (Node.isIdentifier(nameNode)) {
        const scope = enclosingScope(node);
        if (scope) addBinding(scope, nameNode.getText());
      }
      return;
    }
    if (Node.isCatchClause(node)) {
      const decl = node.getVariableDeclaration();
      if (decl) {
        const nameNode = decl.getNameNode();
        if (Node.isIdentifier(nameNode)) {
          addBinding(node, nameNode.getText());
        }
      }
      return;
    }
  });
  return scopeBindings;
}

function isLocallyBound(
  idNode: Node,
  fnNode: Node,
  name: string,
  scopeBindings: Map<Node, Set<string>>,
): boolean {
  let cur: Node | undefined = idNode.getParent();
  while (cur) {
    const names = scopeBindings.get(cur);
    if (names?.has(name)) return true;
    if (cur === fnNode) return false;
    cur = cur.getParent();
  }
  return false;
}

// Filter: identifier nodes that occupy a syntactic "name slot" in their
// parent (property keys, property access names, parameter binding sites,
// import/export specifiers) are NOT reads of a binding. Skip them.
function identifierIsNameSlot(node: Node): boolean {
  const parent = node.getParent();
  if (!parent) return false;
  if (Node.isPropertyAccessExpression(parent) && parent.getNameNode() === node) return true;
  if (Node.isPropertyAssignment(parent) && parent.getNameNode() === node) return true;
  // Note: shorthand property `{x}` IS a real read; not in this filter.
  if (Node.isPropertyDeclaration(parent) && parent.getNameNode() === node) return true;
  if (Node.isPropertySignature(parent) && parent.getNameNode() === node) return true;
  if (Node.isMethodDeclaration(parent) && parent.getNameNode() === node) return true;
  if (Node.isMethodSignature(parent) && parent.getNameNode() === node) return true;
  if (Node.isParameterDeclaration(parent) && parent.getNameNode() === node) return true;
  if (Node.isBindingElement(parent) && parent.getNameNode() === node) return true;
  if (Node.isImportSpecifier(parent)) return true;
  if (Node.isExportSpecifier(parent)) return true;
  return false;
}

// AST-side implementation of `isInsideExpect`. Used during L1 only;
// L2 reads the precomputed `inside_expect` flag from FnEvent records.
function isInsideExpectAst(node: Node): boolean {
  let cur: Node | undefined = node.getParent();
  while (cur !== undefined) {
    if (Node.isCallExpression(cur)) {
      const expr = cur.getExpression();
      if (Node.isIdentifier(expr) && expr.getText() === "expect") return true;
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
  metadata: Map<string, PerFileMetadata>,
  repoKey: string,
): void {
  const symbolIndex = buildLocalSymbolIndex(prims);
  // Side index: primitive id -> primitive kind. Used to gate `extends` /
  // `implements` by the resolved target's actual kind — see #86. Real-world
  // TS often binds a "class" as `const X = factory(...)` (a `variable`
  // primitive); emitting `extends -> variable` with confidence=exact violates
  // EDGE_KIND_RULES, so we soften to confidence=fuzzy in that case.
  const kindById = new Map<string, string>();
  for (const p of prims) kindById.set(p.id, p.primitive);
  for (const [rel, meta] of metadata) {
    for (const cm of meta.classes) {
      const myId = canonicalId(repoKey, rel, cm.name);
      const myPrim = prims.find((p) => p.id === myId);
      if (!myPrim) continue;
      if (cm.extends_name) {
        const targetId = symbolIndex.get(cm.extends_name);
        if (targetId) {
          const targetKind = kindById.get(targetId);
          // class -> class: structural inheritance, exact.
          // class -> variable: factory-binding base (e.g. zod's
          // `const ZodType = createZodType(...)`); inheritance arrow is real
          // but the static taxonomy can't prove it without dataflow, so we
          // downgrade to fuzzy. EDGE_KIND_RULES permits this combination
          // only under fuzzy confidence (#86).
          // class -> function: same pattern but rarer; treat as fuzzy.
          const confidence = targetKind === "class" ? "exact" : "fuzzy";
          myPrim.edges_out.push({
            target: targetId,
            kind: "extends",
            via: "class_decl",
            where: `${rel}:${cm.extends_line}`,
            confidence,
          });
        }
      }
      for (const impl of cm.implements) {
        const targetId = symbolIndex.get(impl.name);
        if (targetId) {
          const targetKind = kindById.get(targetId);
          // `implements` parallels `extends` (#86). A class can implement a
          // type whose binding is a `const`-exported brand/shape; downgrade
          // to fuzzy when the resolved target is not itself a class.
          const confidence = targetKind === "class" ? "exact" : "fuzzy";
          myPrim.edges_out.push({
            target: targetId,
            kind: "implements",
            via: "class_decl",
            where: `${rel}:${impl.line}`,
            confidence,
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
  metadata: Map<string, PerFileMetadata>,
  repoKey: string,
): void {
  // Build symbol index: symbol name -> id (top-level, owner-null)
  // (unused here directly but kept for parity with old build).
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
  // Two-phase build (matches the pre-streaming closure pass): direct named
  // re-exports first, then wildcard expansion via DFS, then a closure pass
  // that collapses chains of synthetic placeholders left by named-only
  // multi-hop chains.
  const namedReexports = new Map<string, Map<string, string>>();
  const wildcardFrom = new Map<string, Set<string>>();
  for (const [rel, meta] of metadata) {
    for (const exp of meta.exports) {
      const targetRel2 = exp.resolved_rel;
      if (!targetRel2) continue;
      if (exp.is_wildcard) {
        if (!wildcardFrom.has(rel)) wildcardFrom.set(rel, new Set());
        wildcardFrom.get(rel)!.add(targetRel2);
        continue;
      }
      const targetSyms2 = symByPath.get(targetRel2) ?? new Map<string, string>();
      for (const spec of exp.named) {
        const symId = targetSyms2.get(spec.name);
        const originId = symId ?? `${repoKey}::${targetRel2}::${spec.name}`;
        if (!namedReexports.has(rel)) namedReexports.set(rel, new Map());
        namedReexports.get(rel)!.set(spec.consumer_name, originId);
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
  for (const [rel] of metadata) {
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

  // Closure pass: collapse multi-hop chains of synthetic re-export ids.
  const MAX_REEXPORT_HOPS = 16;
  for (const exports of reexportMap.values()) {
    for (const [name, id] of exports) {
      let resolved = id;
      for (let hop = 0; hop < MAX_REEXPORT_HOPS; hop++) {
        const idx = resolved.indexOf("::");
        if (idx < 0) break;
        const rest = resolved.slice(idx + 2);
        const innerIdx = rest.lastIndexOf("::");
        if (innerIdx < 0) break;
        const innerFile = rest.slice(0, innerIdx);
        const innerName = rest.slice(innerIdx + 2);
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
  // declaration with the `default` modifier).
  const defaultExportMap = new Map<string, string>();
  for (const [rel, meta] of metadata) {
    const localSyms = symByPath.get(rel);
    if (!localSyms) continue;
    if (meta.default_export_identifier) {
      const id = localSyms.get(meta.default_export_identifier);
      if (id) defaultExportMap.set(rel, id);
    }
    if (defaultExportMap.has(rel)) continue;
    if (meta.default_export_class_or_fn_name) {
      const id = localSyms.get(meta.default_export_class_or_fn_name);
      if (id) defaultExportMap.set(rel, id);
    }
  }

  for (const [rel, meta] of metadata) {
    const modPrim = modByPath.get(rel);
    if (!modPrim) continue;

    for (const imp of meta.imports) {
      const targetRel = imp.resolved_rel;
      const targetSyms = targetRel ? (symByPath.get(targetRel) ?? new Map<string, string>()) : new Map<string, string>();
      const targetReexports = targetRel ? (reexportMap.get(targetRel) ?? new Map<string, string>()) : new Map<string, string>();

      if (imp.default_import) {
        const localBinding = imp.default_import;
        const defaultId = targetRel ? defaultExportMap.get(targetRel) : undefined;
        const externalPkg = npmPkgFromSpec(imp.spec_text);
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
          where: `${rel}:${imp.line}`,
          confidence, local_binding: localBinding,
        });
      }

      if (imp.namespace_import) {
        const localBinding = imp.namespace_import;
        const externalPkg = npmPkgFromSpec(imp.spec_text);
        const target = targetRel
          ? `${repoKey}::${targetRel}`
          : `external::npm::${externalPkg}`;  // #29
        const confidence = targetRel ? "exact" : "unresolved";
        modPrim.edges_out.push({
          target, kind: "imports", via: "import_decl",
          where: `${rel}:${imp.line}`,
          confidence, local_binding: localBinding,
        });
      }

      for (const spec of imp.named) {
        const importedName = spec.name;
        const localBinding = spec.local_binding;
        let target: string;
        let confidence: string;
        if (targetRel) {
          const symId = targetSyms.get(importedName);
          if (symId) {
            target = symId;
            confidence = "exact";
          } else {
            const reexportId = targetReexports.get(importedName);
            if (reexportId) {
              target = reexportId;
              confidence = "fuzzy";
            } else {
              target = `${repoKey}::${targetRel}`;
              confidence = "fuzzy";
            }
          }
        } else {
          const pkgName = npmPkgFromSpec(imp.spec_text);
          target = `external::npm::${pkgName}::${importedName}`;
          confidence = "unresolved";
        }
        modPrim.edges_out.push({
          target, kind: "imports", via: "import_decl",
          where: `${rel}:${imp.line}`,
          confidence, local_binding: localBinding,
        });
      }
    }

    // Re-exports: export { foo } from "./impl.js"
    for (const exp of meta.exports) {
      const targetRel2 = exp.resolved_rel;
      const targetSyms2 = targetRel2 ? (symByPath.get(targetRel2) ?? new Map<string, string>()) : new Map<string, string>();
      const targetReexports2 = targetRel2 ? (reexportMap.get(targetRel2) ?? new Map<string, string>()) : new Map<string, string>();

      const externalPkg = npmPkgFromSpec(exp.spec_text || "");
      for (const spec of exp.named) {
        const exportedName = spec.name;
        const localBinding = spec.consumer_name;
        const symId = targetRel2 ? targetSyms2.get(exportedName) : undefined;
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
          where: `${rel}:${exp.line}`,
          confidence: "fuzzy", local_binding: localBinding,
        });
      }
    }

    // Top-level dynamic imports (`import('./rel')` / `import('pkg')`). The
    // Function-constructor shim form rides on the call_bare events emitted
    // by attachCallAndVarAccessEdges (and was attributed to the enclosing
    // module identically to static imports).
    for (const di of meta.dynamic_imports) {
      if (di.spec_text === null) continue; // non-literal — can't resolve
      const specText = di.spec_text;
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
        where: `${rel}:${di.line}`, confidence,
      });
    }
  }
}

// ---------------------------------------------------------------------------
// L2 edge resolution — Task 3.4/3.5: calls + instantiates (intra-fn type
// binding) + reads/assigns. Drives off the per-function event stream
// captured in L1 — no AST access.
// ---------------------------------------------------------------------------

function attachCallAndVarAccessEdges(
  prims: Primitive[],
  metadata: Map<string, PerFileMetadata>,
  repoKey: string,
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
        const localName = p.name.split(".").pop()!;
        const lookupName = localName.replace(/:static$/, "");
        methodsByClass.get(p.owner)!.set(lookupName, p.id);
      }
    }
  }

  // Primitive-kind index for taxonomy-correct edge emission. `calls` targets
  // must be functions and `instantiates` targets must be classes (per
  // depgraph/lib/edges.py::EDGE_KIND_RULES).
  const allClassIds = new Set(prims.filter((p) => p.primitive === "class").map((p) => p.id));
  const allFunctionIds = new Set(prims.filter((p) => p.primitive === "function").map((p) => p.id));
  // Side index: primitive id -> primitive kind. Used to gate `instantiates`
  // confidence by the resolved target's actual kind — symmetric to the
  // `extends`/`implements` treatment in attachInheritanceEdges (#86). Real
  // TS factory patterns bind a class as `const X = $constructor(...)` (a
  // `variable` primitive); when the source file also declares an interface
  // of the same name the two primitives collide on id and reconcile picks
  // the variable. `new X(...)` then emits `instantiates -> variable` at
  // confidence=exact, which the validator rejects. We downgrade to fuzzy
  // when the resolved target is not itself a class (#88).
  const kindById = new Map<string, string>();
  for (const p of prims) kindById.set(p.id, p.primitive);

  // Local top-level symbol index per file: name -> id (non-method, owner-null)
  const localByPath = new Map<string, Map<string, string>>();
  for (const p of prims) {
    if (p.owner === null && (p.primitive === "class" || p.primitive === "function" || p.primitive === "variable")) {
      if (!localByPath.has(p.source.path)) localByPath.set(p.source.path, new Map());
      localByPath.get(p.source.path)!.set(p.name, p.id);
    }
  }

  // Import bindings per file: local_binding -> target_id (lifted off the
  // imports edges emitted by attachImportsEdges, so the resolver reflects
  // every demotion/promotion that pass applied — node_modules→external, etc).
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

  // Dynamic-import-shim bindings per file (from L1 metadata).
  const importShimsByPath = new Map<string, Set<string>>();
  for (const [rel, meta] of metadata) {
    if (meta.import_shims.length === 0) continue;
    const set = new Set<string>();
    for (const s of meta.import_shims) set.add(s.binding_name);
    importShimsByPath.set(rel, set);
  }

  for (const [rel, meta] of metadata) {
    const localNames = localByPath.get(rel) ?? new Map<string, string>();
    const imports = importsByPath.get(rel) ?? new Map<string, string>();
    const shims = importShimsByPath.get(rel);
    const localVars = varsByPath.get(rel);  // module-scope variables; undefined if file has none

    const resolveClass = (name: string): string | undefined => {
      const id = localNames.get(name) ?? imports.get(name);
      return id && allClassIds.has(id) ? id : undefined;
    };

    for (const fm of meta.functions) {
      const fnPrim = fnByPathAndLine.get(`${rel}:${fm.start_line}`);
      if (!fnPrim) continue;

      // var_types: local variable name -> class id (seeded from parameter
      // type annotations, then refined by per-event var_decl entries).
      const varTypes = new Map<string, string>();
      for (const param of fm.parameters) {
        if (!param.type_name) continue;
        const cid = resolveClass(param.type_name);
        if (cid) varTypes.set(param.name, cid);
      }

      // Replay the event stream in document order — matches the old visitor
      // walk's semantics (var_decl events feed varTypes before later call
      // events consult it; identifier events stand alone).
      for (const ev of fm.events) {
        if (ev.kind === "identifier") {
          if (!localVars) continue;
          const varId = localVars.get(ev.name);
          if (!varId) continue;
          fnPrim.edges_out.push({
            target: varId,
            kind: ev.is_assignment_lhs ? "assigns" : "reads",
            via: ev.is_assignment_lhs ? "assignment_lhs" : "identifier_read",
            where: `${rel}:${ev.line}`,
            confidence: "exact",
          });
          continue;
        }
        if (ev.kind === "var_decl") {
          if (ev.type_name) {
            const cid = resolveClass(ev.type_name);
            if (cid) varTypes.set(ev.name, cid);
          }
          if (ev.new_expr_class_name) {
            const cid = resolveClass(ev.new_expr_class_name);
            if (cid) varTypes.set(ev.name, cid);
          }
          continue;
        }
        if (ev.kind === "new") {
          const targetId = localNames.get(ev.class_name) ?? imports.get(ev.class_name);
          if (targetId) {
            const targetKind = kindById.get(targetId);
            // class -> class instantiation, exact.
            // class -> variable: factory-binding pattern (e.g. zod's
            //   `export const ZodObject = core.$constructor(...)`); the
            //   `new ZodObject(...)` arrow is real but the static taxonomy
            //   can't prove it without dataflow. EDGE_KIND_RULES permits
            //   `instantiates -> variable` ONLY at fuzzy (#88).
            // class -> function: same posture as variable; rare in practice
            //   but treat identically (e.g. `new factory()` where factory
            //   is itself a declared function).
            // Any other / unresolved target: drop (today's behavior).
            if (targetKind === "class") {
              fnPrim.edges_out.push({
                target: targetId, kind: "instantiates", via: "new_expression",
                where: `${rel}:${ev.line}`, confidence: "exact",
              });
            } else if (targetKind === "variable" || targetKind === "function") {
              fnPrim.edges_out.push({
                target: targetId, kind: "instantiates", via: "new_expression",
                where: `${rel}:${ev.line}`, confidence: "fuzzy",
              });
            }
          }
          continue;
        }
        if (ev.kind === "call_dynamic_import") {
          const modPrim = modByPath.get(rel);
          if (!modPrim) continue;
          if (ev.spec_text === null) continue; // non-literal — silently skip
          // The top-level dynamic-import sweep in extractPerFileMetadata
          // already captured every `import(...)` callsite (visitor walked the
          // whole file). To avoid double-emission, attach only the per-fn
          // dynamic-import events that fall *outside* the meta.dynamic_imports
          // line set. But it's cleaner to emit only from the file-level list
          // and ignore per-fn call_dynamic_import events here.
          continue;
        }
        if (ev.kind === "call_bare") {
          const name = ev.callee_name;
          // Dynamic-import-shim: `importESM('mod')` is semantically `import('mod')`.
          if (shims?.has(name)) {
            const modPrim = modByPath.get(rel);
            const specText = ev.first_arg_literal;
            if (modPrim && specText) {
              const target = specText.startsWith(".")
                ? `external::unresolved::${specText}`
                : `external::npm::${npmPkgFromSpec(specText)}`;  // #29
              modPrim.edges_out.push({
                target, kind: "imports", via: "dynamic_import_shim",
                where: `${rel}:${ev.line}`,
                confidence: specText.startsWith(".") ? "unresolved" : "fuzzy",
              });
            }
            continue;
          }
          const targetId = localNames.get(name) ?? imports.get(name);
          const isExternal = targetId?.startsWith("external::");
          if (targetId && (allFunctionIds.has(targetId) || isExternal)) {
            fnPrim.edges_out.push({
              target: targetId, kind: "calls", via: "function_call",
              where: `${rel}:${ev.line}`, confidence: "exact",
            });
          }
          continue;
        }
        if (ev.kind === "call_method") {
          const recvName = ev.receiver_text;
          const methodName = ev.method_name;
          const where = `${rel}:${ev.line}`;
          const recvClassId = varTypes.get(recvName);
          // Baseline behavior: emit a method-call edge only when we can
          // bind the receiver to a class via var_types (parameter annotation
          // or `new Cls()` initializer). Otherwise drop the call silently.
          // The earlier #69 elaboration (imports-table fallback emitting
          // external::unresolved terminals) was reverted in main and isn't
          // restored here.
          if (recvClassId) {
            const methodId = methodsByClass.get(recvClassId)?.get(methodName);
            if (methodId) {
              fnPrim.edges_out.push({
                target: methodId, kind: "calls", via: "method_call",
                where, confidence: "exact",
              });
            } else {
              const className = recvClassId.split("::").pop() ?? recvClassId;
              fnPrim.edges_out.push({
                target: `external::unresolved::${className}.${methodName}`,
                kind: "calls", via: "method_call",
                where, confidence: "unresolved",
              });
            }
          }
          continue;
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
  metadata: Map<string, PerFileMetadata>,
): void {
  // Build local symbol index per file: name -> id (non-method, owner-null)
  const localByPath = new Map<string, Map<string, string>>();
  for (const p of prims) {
    if (p.owner === null && (p.primitive === "class" || p.primitive === "function" || p.primitive === "variable")) {
      if (!localByPath.has(p.source.path)) localByPath.set(p.source.path, new Map());
      localByPath.get(p.source.path)!.set(p.name, p.id);
    }
  }

  // Build import bindings per file (lifted off the imports edges, post-pass).
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

  for (const [rel, meta] of metadata) {
    if (!isTestPath(rel)) continue;
    const localNames = localByPath.get(rel) ?? new Map<string, string>();
    const imports = importsByPath.get(rel) ?? new Map<string, string>();

    for (const fm of meta.functions) {
      const fnPrim = fnByPathAndLine.get(`${rel}:${fm.start_line}`);
      if (!fnPrim) continue;

      // Replay call events: bare + method calls whose `inside_expect` flag
      // was set at L1. Mirrors the old visitor walk's semantics exactly.
      for (const ev of fm.events) {
        let calleeName: string | null = null;
        let line: number;
        if (ev.kind === "call_bare") {
          if (!ev.inside_expect) continue;
          calleeName = ev.callee_name;
          line = ev.line;
        } else if (ev.kind === "call_method") {
          if (!ev.inside_expect) continue;
          calleeName = ev.method_name;
          line = ev.line;
        } else {
          continue;
        }
        if (!calleeName || TS_TEST_FRAMEWORK_PRIMITIVES.has(calleeName)) continue;
        const targetId = localNames.get(calleeName) ?? imports.get(calleeName);
        if (targetId && !targetId.startsWith("external::")) {
          fnPrim.edges_out.push({
            target: targetId, kind: "tests", via: "asserted_call",
            where: `${rel}:${line}`, confidence: "exact",
          });
        }
      }
    }
  }
}

// reads/assigns: folded into attachCallAndVarAccessEdges via the FnEvent stream
// (see issue #47). Identifier events carry the assignment-lhs flag.

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
  // Visitor-based walk; each visited Node is released to GC after the
  // callback returns.
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

  // Build the rel-path list up front (used for package primitives + as the
  // driver for deterministic L2 iteration order).
  const relPaths: string[] = sourceFiles.map((sf) => relative(repoPath, sf.getFilePath()));

  // ---- L1a: cross-file specifier resolution (BEFORE any sf.forget()) ----
  //
  // ts-morph's `imp.getModuleSpecifierSourceFile()` traverses the Project's
  // file graph; forgetting any target file makes its consumers' resolution
  // return null. So we resolve every import/export specifier up front while
  // all source files are still loaded, then forget files in the heavy loop
  // below. Captures tsconfig path-alias resolution along with plain
  // relative/absolute resolution.
  const resolvedSpecsByPath = buildResolvedSpecMap(sourceFiles, repoPath);

  // ---- L1b: per-file primitives + metadata + sf.forget() ----
  //
  // The streaming refactor (issue #47). Each iteration:
  //   1. Emit primitives (module/classes/functions/variables/object-literal
  //      classes/route_call) for this file.
  //   2. Capture PerFileMetadata so L2 doesn't need the AST.
  //   3. Forget the SourceFile — releases the AST so its memory is reclaimed
  //      before the next file is processed.
  const allPrims: Primitive[] = [];
  const metadata = new Map<string, PerFileMetadata>();
  // Insertion order is the sourceFiles order; the Map preserves it for L2.
  for (const p of packagePrimitivesFromRelPaths(relPaths, repoKey)) allPrims.push(p);
  for (const sf of sourceFiles) {
    const relPath = relative(repoPath, sf.getFilePath());
    const resolvedSpecs = resolvedSpecsByPath.get(relPath) ?? { imports: [], exports: [] };
    allPrims.push(moduleFor(sf, repoKey, repoPath));
    for (const p of extractClasses(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractFunctions(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractVariables(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractDefaultExport(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractObjectLiteralApiClients(sf, repoKey, relPath)) allPrims.push(p);
    for (const p of extractRouteCalls(sf, repoKey, relPath)) allPrims.push(p);
    metadata.set(relPath, extractPerFileMetadata(sf, repoPath, relPath, resolvedSpecs));
    // Drop the AST. Subsequent L2 passes never touch sourceFiles again.
    sf.forget();
  }

  // ---- L2: AST-free edge resolution ----
  attachDefinesEdges(allPrims);
  attachInheritanceEdges(allPrims, metadata, repoKey);
  attachImportsEdges(allPrims, metadata, repoKey);
  // calls + instantiates + reads/assigns share one per-fn event-replay loop.
  attachCallAndVarAccessEdges(allPrims, metadata, repoKey);
  attachTestsEdges(allPrims, metadata);

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
