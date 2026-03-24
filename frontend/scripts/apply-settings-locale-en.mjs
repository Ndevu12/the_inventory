/**
 * Overlays English SettingsTenant / SettingsPlatform onto public/locales/en.json.
 * Run from frontend/: node scripts/apply-settings-locale-en.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const enPath = join(__dirname, "../public/locales/en.json");
const overlay = JSON.parse(
  readFileSync(join(__dirname, "settings-locale-en.json"), "utf-8"),
);

const data = JSON.parse(readFileSync(enPath, "utf-8"));
data.SettingsTenant = overlay.SettingsTenant;
data.SettingsPlatform = overlay.SettingsPlatform;
writeFileSync(enPath, `${JSON.stringify(data, null, 2)}\n`, "utf-8");
console.log("Applied English settings overlay to en.json");
