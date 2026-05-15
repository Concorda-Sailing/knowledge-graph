import { describe, it, expect } from "vitest";
import * as fs from "fs";
import * as path from "path";
import {
  slugifyIdTs, sha, canonicalIdForRepoSymbol,
} from "../../extractors/generic/typescript/canonical";

describe("typescript canonical helpers", () => {
  it("slugifyIdTs matches pre-flip component filename", () => {
    expect(slugifyIdTs("concorda-web::src/app/code-of-conduct/page.tsx::CodeOfConductPage"))
      .toBe("concorda_web__src_app_code_of_conduct_page_tsx__CodeOfConductPage");
  });

  it("slugifyIdTs matches pre-flip test filename", () => {
    expect(slugifyIdTs("concorda-test::tests/admin/club-management.spec.ts::test@12"))
      .toBe("concorda_test__tests_admin_club_management_spec_ts__test_12");
  });

  it("sha reproduces pre-flip component hash", () => {
    const text = fs.readFileSync(
      path.join(__dirname, "fixtures/pre_flip_nodes/component__sample_text.txt"),
      "utf8",
    );
    const payload = { name: "CodeOfConductPage", kind: "component", text };
    expect(sha(payload)).toBe(
      "90b1d7839d61794ad7897fee587ebdbee97a4cb43885ce94d9f325c53c3255c1",
    );
  });

  it("canonicalIdForRepoSymbol", () => {
    expect(canonicalIdForRepoSymbol("concorda-web", "src/x.tsx", "Foo"))
      .toBe("concorda-web::src/x.tsx::Foo");
  });

});
