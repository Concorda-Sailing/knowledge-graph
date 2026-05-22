import { createHash } from "node:crypto";

export function canonicalId(repo: string, path: string, symbol: string): string {
  return `${repo}::${path}::${symbol}`;
}

// Per-id slug. Must stay bit-identical with
// depgraph/lib/primitives.py::slugify_id_for_filename (the Python writer/reader
// both use the lib function; this mirror exists for extractor-language
// consistency). Appends an 8-char sha1 suffix when the id contains characters
// outside the structurally-safe set `[a-zA-Z0-9_/.:]` so that ids like
// `r::v4-mini` and `r::v4/mini`, or `m.ts` and `m.ts::$`, get distinct on-disk
// filenames (#87).
const SAFE_SLUG_CHAR_RE = /^[a-zA-Z0-9_/.:]*$/;

export function slugifyId(nodeId: string): string {
  const bare = nodeId
    .replace(/::/g, "__")
    .replace(/[^a-zA-Z0-9_]/g, "_")
    .replace(/^_+|_+$/g, "");
  if (!SAFE_SLUG_CHAR_RE.test(nodeId)) {
    const h = createHash("sha1").update(nodeId).digest("hex").slice(0, 8);
    return bare ? `${bare}_${h}` : h;
  }
  return bare;
}

/** sha256 of canonical-JSON (keys sorted recursively) of the payload. */
export function structuralHash(payload: unknown): string {
  return createHash("sha256").update(canonicalJSON(payload)).digest("hex");
}

function canonicalJSON(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(canonicalJSON).join(",")}]`;
  }
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalJSON(obj[k])}`).join(",")}}`;
}
