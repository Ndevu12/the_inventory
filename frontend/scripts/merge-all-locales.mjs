/**
 * Runs every locale merge in order. Single entry point for `yarn locale:merge`.
 *
 * 1. Inventory → public/locales/*.json
 * 2. Sales → public/locales/*.json
 * 3. Reports → public/locales/*.json
 * 4. Auth + Audit → public/locales/{fr,es,ar,rw,sw}.json
 * 5. Settings (English overlay) → public/locales/en.json
 * 6. Rebuild en.json from English artifacts (key tree checked against fr, not fr copy)
 */
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const steps = [
  "merge-inventory-locale.mjs",
  "merge-sales-locale.mjs",
  "merge-reports-locale.mjs",
  "merge-auth-audit-locale.mjs",
  "apply-settings-locale-en.mjs",
  "rebuild-en-locale.mjs",
];

for (const file of steps) {
  const scriptPath = join(__dirname, file);
  const result = spawnSync(process.execPath, [scriptPath], {
    stdio: "inherit",
    env: process.env,
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

console.log("\nAll locale merges finished.");
