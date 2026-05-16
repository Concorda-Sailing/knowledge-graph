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

  // Build re-export map: module rel-path -> {exportedName -> origin-symbol-id}
  // This allows one-hop re-export resolution for consumers of barrels.
  const reexportMap = new Map<string, Map<string, string>>();
  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    for (const exp of sf.getExportDeclarations()) {
      if (!exp.hasModuleSpecifier()) continue;
      const targetSf2 = exp.getModuleSpecifierSourceFile();
      const targetRel2 = targetSf2 ? relative(repoPath, targetSf2.getFilePath()) : null;
      if (!targetRel2) continue;
      const targetSyms2 = symByPath.get(targetRel2) ?? new Map();
      for (const spec of exp.getNamedExports()) {
        const exportedName = spec.getName();
        const symId = targetSyms2.get(exportedName);
        const originId = symId ?? `${repoKey}::${targetRel2}::${exportedName}`;
        if (!reexportMap.has(rel)) reexportMap.set(rel, new Map());
        reexportMap.get(rel)!.set(exportedName, originId);
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
        const target = targetRel
          ? `${repoKey}::${targetRel}::default`
          : `external::npm::unknown::default`;
        const confidence = targetRel ? "exact" : "unresolved";
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

      for (const spec of exp.getNamedExports()) {
        const exportedName = spec.getName();
        const aliasNode = spec.getAliasNode();
        const localBinding = aliasNode ? aliasNode.getText() : exportedName;
        const symId = targetRel2 ? targetSyms2.get(exportedName) : undefined;
        const target = symId
          ? symId
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

  for (const sf of sourceFiles) {
    const rel = relative(repoPath, sf.getFilePath());
    const localNames = localByPath.get(rel) ?? new Map<string, string>();
    const imports = importsByPath.get(rel) ?? new Map<string, string>();

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

function main() {
  const { values } = parseArgs({
    options: {
      "repo-key": { type: "string" },
      "repo-path": { type: "string" },
      "format": { type: "string", default: "ndjson" },
    },
  });
  const repoKey = values["repo-key"];
  const repoPath = values["repo-path"];
  if (!repoKey || !repoPath) {
    console.error("Usage: extract.ts --repo-key <key> --repo-path <path>");
    process.exit(1);
  }

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
    return !fp.includes("/node_modules/") && !fp.includes("/.git/");
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

  for (const p of allPrims) emit(p);
}

main();
