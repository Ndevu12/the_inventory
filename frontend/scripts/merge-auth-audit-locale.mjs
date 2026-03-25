/**
 * Overlays translated `Auth` and `Audit` from `auth-audit-locale-payload.json`
 * onto `public/locales/{fr,es,ar,rw,sw}.json`. English (`en.json`) is the source
 * of truth and is not modified here.
 *
 * `Audit` includes tenant log copy: `summary` / `scope` columns,
 * `detail.summary` / `eventScope`, `eventScope.*`, and full `actionLabels` (backend enum parity).
 * Update `auth-audit-locale-en.json` when changing English audit keys, then `rebuild-en-locale.mjs`.
 *
 * Run from frontend/: node scripts/merge-auth-audit-locale.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const payload = JSON.parse(
  readFileSync(join(__dirname, "auth-audit-locale-payload.json"), "utf-8"),
);

for (const code of ["fr", "es", "ar", "rw", "sw"]) {
  const bundle = payload[code];
  if (!bundle?.Auth || !bundle?.Audit) {
    console.warn(`merge-auth-audit-locale: skip ${code} (missing Auth or Audit)`);
    continue;
  }
  const path = join(__dirname, "..", "public", "locales", `${code}.json`);
  const data = JSON.parse(readFileSync(path, "utf-8"));
  data.Auth = bundle.Auth;
  data.Audit = bundle.Audit;
  writeFileSync(path, `${JSON.stringify(data, null, 2)}\n`);
}

console.log("Merged Auth + Audit for: fr, es, ar, rw, sw");
