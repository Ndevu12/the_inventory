/**
 * Merges per-locale `Reports` from `reports-locale-payload.json` into each
 * `public/locales/{code}.json`. Run from frontend/: node scripts/merge-reports-locale.mjs
 *
 * Previously this file wrote English to every locale; use payload[code] so
 * fr/es/ar (and rw/sw) get the correct strings.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const payload = JSON.parse(
  readFileSync(join(__dirname, "reports-locale-payload.json"), "utf-8"),
);

const codes = ["en", "fr", "es", "ar", "rw", "sw"];

for (const code of codes) {
  const path = join(__dirname, "..", "public", "locales", `${code}.json`);
  const data = JSON.parse(readFileSync(path, "utf-8"));
  const reports = payload[code] ?? payload.en;
  if (!reports) {
    throw new Error(`reports-locale-payload.json missing "${code}" and "en"`);
  }
  data.Reports = reports;
  writeFileSync(path, `${JSON.stringify(data, null, 2)}\n`);
}

console.log(`Merged Reports for: ${codes.join(", ")}`);
