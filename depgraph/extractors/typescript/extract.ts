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

  const project = new Project({ skipAddingFilesFromTsConfig: true });
  for (const f of listSourceFiles(repoPath)) project.addSourceFileAtPath(f);

  for (const sf of project.getSourceFiles()) {
    const relPath = relative(repoPath, sf.getFilePath());
    emit(moduleFor(sf, repoKey, repoPath));
    for (const p of extractClasses(sf, repoKey, relPath)) emit(p);
  }
}

main();
