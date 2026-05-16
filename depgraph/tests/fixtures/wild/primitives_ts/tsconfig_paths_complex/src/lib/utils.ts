// Fixture: tsconfig_paths_complex — utilities accessed via ~lib/utils alias
// Also reachable via the more specific ~lib/utils alias that exactly matches this file.

export function formatDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function truncate(str: string, max: number): string {
  return str.length > max ? str.slice(0, max) + "…" : str;
}
