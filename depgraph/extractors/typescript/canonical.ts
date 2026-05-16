import { createHash } from "node:crypto";

export function canonicalId(repo: string, path: string, symbol: string): string {
  return `${repo}::${path}::${symbol}`;
}

export function slugifyId(nodeId: string): string {
  return nodeId
    .replace(/::/g, "__")
    .replace(/[^a-zA-Z0-9_]/g, "_")
    .replace(/^_+|_+$/g, "");
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
