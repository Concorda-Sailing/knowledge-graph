#!/usr/bin/env -S npx tsx
/**
 * extract_expo.ts — analogous to extract_web.ts but for concorda-expo.
 *
 * Differences from web:
 *   - Components are screens (in src/screens/) and may use react-navigation params
 *     rather than Next.js routing.
 *   - The HTTP base URL comes from a config module, not the same origin — call
 *     sites usually look like `api.get('/profile')` where `api` is a configured
 *     client. Canonicalization needs to know about that prefix elision.
 *   - **External consumers risk is highest here**: any released TestFlight or
 *     App Store build is pinned to whatever endpoint contracts existed at build
 *     time. Reconciler must merge expo-discovered consumers into the relevant
 *     endpoint node's `external_consumers` field with a release-version tag.
 *
 * The bulk of the implementation is shared with extract_web.ts; this file
 * thin-wraps that logic with expo-specific path config. TODO(impl): factor out
 * a shared `extract_ts_common.ts` once both stabilize.
 */

import { Project, SourceFile } from "ts-morph";
import * as path from "node:path";

const REPO = process.env.CONCORDA_EXPO_PATH ?? path.join(process.env.HOME!, "concorda-expo");

// TODO(impl): this is a placeholder. Real implementation imports the shared
// extractor functions from extract_ts_common.ts and runs them with REPO above
// + repo: "concorda-expo" + dossier prefix change. Kept as a stub so the
// design is visible without duplicating the full body.

function main() {
  const project = new Project({
    tsConfigFilePath: path.join(REPO, "tsconfig.json"),
    skipAddingFilesFromTsConfig: false,
  });
  let count = 0;
  for (const sf of project.getSourceFiles()) {
    if (sf.getFilePath().includes("node_modules")) continue;
    count++;
  }
  console.log(`extract_expo.ts: SKELETON — found ${count} source files; full extraction TODO(impl)`);
}

main();
