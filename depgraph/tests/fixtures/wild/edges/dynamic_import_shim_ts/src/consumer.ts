// TS-ESM-in-CJS escape hatch: tsc rewrites `import()` to `require()` in CJS,
// so authors hide a real dynamic import behind a Function constructor.
const importESM = new Function('specifier', 'return import(specifier)') as
  (specifier: string) => Promise<unknown>;

export async function loadPkg(): Promise<unknown> {
  return await importESM('@some-scope/some-pkg');
}

export async function loadOther(): Promise<unknown> {
  return await importESM('plain-pkg');
}
