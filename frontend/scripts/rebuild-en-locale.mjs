/**
 * Rebuilds `public/locales/en.json` with English-only sources, then checks key-tree
 * parity against `fr.json` (French is the shape reference for other locales, not the
 * English copy source).
 *
 * Run from repo root: node frontend/scripts/rebuild-en-locale.mjs
 * Or: cd frontend && node scripts/rebuild-en-locale.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(__dirname, "..");

function readJson(rel) {
  return JSON.parse(readFileSync(join(__dirname, rel), "utf-8"));
}

function keyPaths(a, b, prefix = "") {
  const issues = [];
  if (typeof a !== typeof b) {
    issues.push(`${prefix}: type mismatch`);
    return issues;
  }
  if (a === null || b === null) {
    if (a !== b) issues.push(`${prefix}: null mismatch`);
    return issues;
  }
  if (typeof a === "string") return issues;
  if (Array.isArray(a)) {
    if (a.length !== b.length) issues.push(`${prefix}: array length`);
    return issues;
  }
  const ak = Object.keys(a).sort();
  const bk = Object.keys(b).sort();
  for (const k of ak) {
    if (!bk.includes(k)) issues.push(`${prefix}: missing in b: ${k}`);
  }
  for (const k of bk) {
    if (!ak.includes(k)) issues.push(`${prefix}: missing in a: ${k}`);
  }
  for (const k of ak) {
    if (bk.includes(k)) {
      issues.push(...keyPaths(a[k], b[k], `${prefix}.${k}`));
    }
  }
  return issues;
}

const fr = readJson("../public/locales/fr.json");
const core = readJson("locale-en-core.json");
const featuresEn = readJson("locale-en-features.json");
const procurementEn = readJson("procurement-en.json");
const authAudit = readJson("auth-audit-locale-en.json");
const inventoryEn = readJson("inventory-en.json");
const salesPayload = readJson("sales-locale-payload.json");
const reportsPayload = readJson("reports-locale-payload.json");
const settingsEn = readJson("settings-locale-en.json");

const en = structuredClone(fr);

for (const [k, v] of Object.entries(core)) {
  en[k] = structuredClone(v);
}

en.Reservations = structuredClone(featuresEn.Reservations);
en.CycleCounts = structuredClone(featuresEn.CycleCounts);
en.BulkOperations = structuredClone(featuresEn.BulkOperations);
en.Inventory = structuredClone(inventoryEn);
en.Sales = structuredClone(salesPayload.en);
en.Reports = structuredClone(reportsPayload.en);
en.SettingsTenant = structuredClone(settingsEn.SettingsTenant);
en.SettingsPlatform = structuredClone(settingsEn.SettingsPlatform);
en.Auth = structuredClone(authAudit.Auth);
en.Audit = structuredClone(authAudit.Audit);
en.Procurement = structuredClone(procurementEn);

const outPath = join(frontendRoot, "public", "locales", "en.json");
writeFileSync(outPath, `${JSON.stringify(en, null, 2)}\n`, "utf-8");

const parity = keyPaths(fr, en);
if (parity.length) {
  console.error("Key parity issues:", parity.slice(0, 30));
  process.exit(1);
}

console.log("Wrote", outPath, "(key tree matches fr.json)");
