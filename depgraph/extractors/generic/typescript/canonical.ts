import { createHash } from "node:crypto";

/** Pure helpers for converting AST primitives into canonical depgraph nodes.
 *  Pinned to pre-flip extract_web.ts / extract_tests.ts output byte-for-byte.
 *  See plan: docs/superpowers/plans/2026-05-15-framework-canonicalization.md. */

/** TS slugify (extract_web.ts:72-74).
 *  More aggressive than Python's: replaces ALL non-[a-zA-Z0-9_] with `_`. */
export function slugifyIdTs(nodeId: string): string {
  let s = nodeId.replace(/::/g, "__");
  s = s.replace(/[^a-zA-Z0-9_]/g, "_");
  s = s.replace(/^_+|_+$/g, "");
  return s;
}

/** extract_web.ts:76-78 — sha256 of JSON.stringify (insertion order, no sort). */
export function sha(payload: unknown): string {
  return createHash("sha256").update(JSON.stringify(payload)).digest("hex");
}

export function canonicalIdForRepoSymbol(
  repoKey: string,
  relPath: string,
  symbol: string,
): string {
  return `${repoKey}::${relPath}::${symbol}`;
}

