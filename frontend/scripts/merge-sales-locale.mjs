import { readFileSync, writeFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const __dirname = dirname(fileURLToPath(import.meta.url))
const payload = JSON.parse(
  readFileSync(join(__dirname, "sales-locale-payload.json"), "utf-8"),
)

for (const code of ["en", "fr", "es", "ar", "rw", "sw"]) {
  const path = join(__dirname, "..", "public", "locales", `${code}.json`)
  const data = JSON.parse(readFileSync(path, "utf-8"))
  data.Sales = payload[code]
  writeFileSync(path, `${JSON.stringify(data, null, 2)}\n`)
}
