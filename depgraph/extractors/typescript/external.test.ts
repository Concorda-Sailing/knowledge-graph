import { describe, expect, it } from "vitest";
import {
  inNodeModules,
  npmPkgFromNodeModulesRel,
  npmPkgFromSpec,
} from "./extract.js";

describe("inNodeModules", () => {
  it("detects rels under node_modules/", () => {
    expect(inNodeModules("node_modules/react/index.d.ts")).toBe(true);
  });

  it("detects nested node_modules/", () => {
    expect(inNodeModules("packages/web/node_modules/react/index.d.ts")).toBe(true);
  });

  it("does not match repo files that just happen to contain the word", () => {
    expect(inNodeModules("src/node_modules_notes.md")).toBe(false);
    expect(inNodeModules("src/components/Button.tsx")).toBe(false);
  });

  it("handles null safely", () => {
    expect(inNodeModules(null)).toBe(false);
  });
});

describe("npmPkgFromSpec", () => {
  it("preserves unscoped package", () => {
    expect(npmPkgFromSpec("react")).toBe("react");
    expect(npmPkgFromSpec("react-native")).toBe("react-native");
  });

  it("preserves scoped package as `@scope/name`", () => {
    expect(npmPkgFromSpec("@react-navigation/native")).toBe("@react-navigation/native");
  });

  it("drops sub-path imports", () => {
    expect(npmPkgFromSpec("@scope/pkg/sub/path")).toBe("@scope/pkg");
    expect(npmPkgFromSpec("react/jsx-runtime")).toBe("react");
  });

  it("returns 'local' for relative specs", () => {
    expect(npmPkgFromSpec("./helpers")).toBe("local");
    expect(npmPkgFromSpec("../utils")).toBe("local");
  });
});

describe("npmPkgFromNodeModulesRel", () => {
  it("extracts unscoped package", () => {
    expect(npmPkgFromNodeModulesRel("node_modules/react/index.d.ts")).toBe("react");
    expect(npmPkgFromNodeModulesRel("node_modules/react-native/types/index.d.ts"))
      .toBe("react-native");
  });

  it("preserves scope in scoped packages", () => {
    expect(
      npmPkgFromNodeModulesRel(
        "node_modules/@react-navigation/native/lib/typescript/src/index.d.ts",
      ),
    ).toBe("@react-navigation/native");
  });

  it("redirects @types/<pkg> to <pkg> (DefinitelyTyped convention)", () => {
    expect(npmPkgFromNodeModulesRel("node_modules/@types/react/index.d.ts"))
      .toBe("react");
  });

  it("returns null when not under node_modules", () => {
    expect(npmPkgFromNodeModulesRel("src/foo.ts")).toBeNull();
  });
});
