import { readFile } from "node:fs/promises";
import path from "node:path";

import { routing } from "./routing";

export async function loadMessages(
  locale: string,
): Promise<Record<string, unknown>> {
  const filePath = path.join(
    process.cwd(),
    "public",
    "locales",
    `${locale}.json`,
  );
  try {
    const raw = await readFile(filePath, "utf-8");
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    if (locale !== routing.defaultLocale) {
      return loadMessages(routing.defaultLocale);
    }
    return {};
  }
}
