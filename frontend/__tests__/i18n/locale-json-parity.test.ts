import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/** I18N feature namespaces that must stay in sync across all UI locales (I18N-04, I18N-09). */
const FEATURE_NAMESPACES = [
  "Nav",
  "Breadcrumbs",
  "Reservations",
  "Reports",
  "CycleCounts",
  "BulkOperations",
  "Procurement",
  "Sales",
  "Auth",
  "Audit",
  "SettingsTenant",
  "SettingsPlatform",
] as const;

function collectLeafKeyPaths(value: unknown, prefix = ""): string[] {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return prefix ? [prefix] : [];
  }
  const out: string[] = [];
  for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
    const p = prefix ? `${prefix}.${k}` : k;
    if (v !== null && typeof v === "object" && !Array.isArray(v)) {
      out.push(...collectLeafKeyPaths(v, p));
    } else {
      out.push(p);
    }
  }
  return out.sort();
}

function featureKeyPaths(data: unknown): Set<string> {
  const root = data as Record<string, unknown>;
  const paths: string[] = [];
  for (const ns of FEATURE_NAMESPACES) {
    expect(root).toHaveProperty(ns);
    paths.push(...collectLeafKeyPaths(root[ns], ns));
  }
  return new Set(paths);
}

describe("public/locales feature namespace parity (Nav, Breadcrumbs, Reservations, Reports, CycleCounts, BulkOperations, Procurement, Sales, Auth, Audit, SettingsTenant, SettingsPlatform)", () => {
  const localesDir = join(process.cwd(), "public", "locales");
  const files = readdirSync(localesDir).filter((f) => f.endsWith(".json"));

  const enData = JSON.parse(
    readFileSync(join(localesDir, "en.json"), "utf-8"),
  ) as unknown;
  const enKeys = featureKeyPaths(enData);

  for (const file of files) {
    if (file === "en.json") continue;

    it(`${file} matches en.json keys under ${FEATURE_NAMESPACES.join(", ")}`, () => {
      const data = JSON.parse(
        readFileSync(join(localesDir, file), "utf-8"),
      ) as unknown;
      const keys = featureKeyPaths(data);
      expect(keys).toEqual(enKeys);
    });
  }
});
