// Fixture: tsconfig_paths_complex — entry point
// Uses multiple overlapping path aliases. Phase 1 captures primitives only; imports ignored.
import { formatDate } from "~lib/utils";
import { Card } from "@/components/Card";

export function bootstrap(): void {
  const d = formatDate(new Date());
  console.log(d);
}
