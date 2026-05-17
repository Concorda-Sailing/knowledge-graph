// Plain dynamic imports — no Function-constructor shim. The extractor must
// emit `imports` edges on the enclosing module for both forms.

export async function loadLocal() {
  const helper = await import("./helper");
  return helper.value;
}

export async function loadPkg() {
  return await import("some-pkg");
}

export async function loadScoped() {
  return await import("@some-scope/some-pkg");
}

// Non-literal spec — dynamic; the extractor must skip this rather than emit
// a wrong edge.
const which = "helper";
export async function loadDynamic() {
  return await import(`./${which}`);
}
