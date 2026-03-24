/**
 * Merges `inventory-by-locale.json` into each `public/locales/{code}.json`.
 * Run from repo root: node frontend/scripts/merge-inventory-locale.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const localesDir = path.join(root, "public", "locales");
const codes = ["en", "fr", "sw", "rw", "es", "ar"];

const bundle = {};
for (const code of codes) {
  const p = path.join(__dirname, `inventory-${code}.json`);
  bundle[code] = JSON.parse(readFileSync(p, "utf-8"));
}

for (const code of codes) {
  const filePath = path.join(localesDir, `${code}.json`);
  const data = JSON.parse(readFileSync(filePath, "utf-8"));
  data.Inventory = bundle[code];
  writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf-8");
}
