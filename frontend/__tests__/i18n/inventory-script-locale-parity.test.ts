import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/** Leaf string paths under inventory-*.json in scripts/ (merged into each locale's Inventory namespace). */
function collectLeafKeyPaths(value: unknown, prefix = ""): string[] {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return prefix ? [prefix] : [];
  }
  const out: string[] = [];
  for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
    const p = prefix ? prefix + "." + k : k;
    if (v !== null && typeof v === "object" && !Array.isArray(v)) {
      out.push(...collectLeafKeyPaths(v, p));
    } else {
      out.push(p);
    }
  }
  return out.sort();
}

describe("scripts/inventory-*.json key parity (locale merge source artifacts)", () => {
  const scriptsDir = join(process.cwd(), "scripts");
  const enPath = join(scriptsDir, "inventory-en.json");
  const enData = JSON.parse(readFileSync(enPath, "utf-8")) as unknown;
  const enKeys = new Set(collectLeafKeyPaths(enData));

  const files = readdirSync(scriptsDir).filter(
    (f) => f.startsWith("inventory-") && f.endsWith(".json"),
  );

  for (const file of files) {
    if (file === "inventory-en.json") continue;

    it(file + " matches inventory-en.json leaf key paths", () => {
      const data = JSON.parse(
        readFileSync(join(scriptsDir, file), "utf-8"),
      ) as unknown;
      const keys = new Set(collectLeafKeyPaths(data));
      expect(keys).toEqual(enKeys);
    });
  }
});
