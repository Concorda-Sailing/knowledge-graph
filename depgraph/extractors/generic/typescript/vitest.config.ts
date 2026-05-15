import { defineConfig } from "vitest/config";
import * as path from "path";

export default defineConfig({
  test: {
    include: ["../../../tests/extractors/test_typescript_canonical.ts"],
    environment: "node",
  },
});
