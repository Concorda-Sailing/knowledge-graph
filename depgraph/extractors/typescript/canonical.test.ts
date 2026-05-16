import { describe, expect, it } from "vitest";
import { canonicalId, slugifyId, structuralHash } from "./canonical.js";

describe("canonical", () => {
  it("builds top-level id", () => {
    expect(canonicalId("concorda-web", "src/foo.ts", "Foo"))
      .toBe("concorda-web::src/foo.ts::Foo");
  });

  it("builds class member id with dot", () => {
    expect(canonicalId("concorda-web", "src/foo.ts", "Foo.bar"))
      .toBe("concorda-web::src/foo.ts::Foo.bar");
  });

  it("slugify replaces non-alphanumeric with underscore", () => {
    expect(slugifyId("concorda-web::src/foo.ts::Foo.bar"))
      .toBe("concorda_web__src_foo_ts__Foo_bar");
  });

  it("structuralHash is sha256 of canonical JSON", () => {
    const h = structuralHash({ name: "x", signature: { return_type: null } });
    expect(h).toMatch(/^[a-f0-9]{64}$/);
  });

  it("structuralHash is stable across key insertion order", () => {
    const a = structuralHash({ a: 1, b: 2 });
    const b = structuralHash({ b: 2, a: 1 });
    expect(a).toBe(b);
  });
});
