import { describe, expect, it } from "vitest";
import { canonicalId, slugifyId, structuralHash } from "./canonical.js";

describe("canonical", () => {
  it("builds top-level id", () => {
    expect(canonicalId("acme-web", "src/foo.ts", "Foo"))
      .toBe("acme-web::src/foo.ts::Foo");
  });

  it("builds class member id with dot", () => {
    expect(canonicalId("acme-web", "src/foo.ts", "Foo.bar"))
      .toBe("acme-web::src/foo.ts::Foo.bar");
  });

  it("slugify keeps bare form when only safe chars are present", () => {
    // Ids whose only special chars are `/`, `.`, and `::` keep a bare slug.
    expect(slugifyId("acmeweb::src/foo.ts::Foo.bar"))
      .toBe("acmeweb__src_foo_ts__Foo_bar");
  });

  it("slugify appends short hash when id contains lossy chars (#87)", () => {
    // `-` is outside the safe set, so the slug gets an 8-char sha1 suffix to
    // keep distinct ids distinct on disk (e.g. `v4-mini` vs `v4/mini`).
    const slug = slugifyId("acme-web::src/foo.ts::Foo.bar");
    expect(slug.startsWith("acme_web__src_foo_ts__Foo_bar_")).toBe(true);
    const suffix = slug.split("_").pop()!;
    expect(suffix).toMatch(/^[a-f0-9]{8}$/);
  });

  it("slugifyId disambiguates `/` vs `-` collision (#87)", () => {
    // Pattern 1: distinct dir/path layouts that the bare slug collapsed.
    const a = slugifyId("r::pkg/v4-mini");
    const b = slugifyId("r::pkg/v4/mini");
    expect(a).not.toBe(b);
  });

  it("slugifyId disambiguates module vs module::$ collision (#87)", () => {
    // Pattern 2: trailing `$` symbol got stripped, collapsing to bare module.
    const a = slugifyId("r::pkg/index.ts");
    const b = slugifyId("r::pkg/index.ts::$");
    expect(a).not.toBe(b);
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
