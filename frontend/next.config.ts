import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadDotenv } from "dotenv";

// Config dir: always frontend/ (where .env.local lives), regardless of process.cwd()
const configDir = path.dirname(fileURLToPath(import.meta.url));
const isDev = process.env.NODE_ENV !== "production";

// Load env files and merge parsed values (Next.js order). Using the parsed result
// directly because process.env may not reflect dotenv's changes when Next.js runs
// the config in a worker process.
const envPaths = [
  path.join(configDir, ".env"),
  ...(isDev
    ? [path.join(configDir, ".env.development")]
    : [path.join(configDir, ".env.production")]),
  path.join(configDir, ".env.local"),
  ...(isDev
    ? [path.join(configDir, ".env.development.local")]
    : [path.join(configDir, ".env.production.local")]),
];

const parsed: Record<string, string> = {};
for (const envPath of envPaths) {
  try {
    const result = loadDotenv({ path: envPath });
    if (result.parsed) {
      Object.assign(parsed, result.parsed);
    }
  } catch {
    // Silently ignore errors when .env file doesn't exist or can't be read
  }
}

// Construct the backend API server URL for rewrites.
// Priority: parsed env (from loaded files) > process.env > fallback
const apiServerUrl =
  parsed.API_SERVER_URL ?? process.env.API_SERVER_URL ?? "http://localhost:8000";

// Validate the API server URL.
function validateUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    console.error(`[next.config] Invalid API_SERVER_URL: "${url}". Expected format: http://localhost:8000 or https://api.example.com`);
    process.exit(1);
  }
}

validateUrl(apiServerUrl);

const nextConfig: NextConfig = {
  // Django expects trailing slashes. Without this, Next.js redirects /api/v1/x/ → /api/v1/x,
  // then Django redirects back → /api/v1/x/ → endless loop (ERR_TOO_MANY_REDIRECTS).
  trailingSlash: true,
  async rewrites() {
    return {
      // beforeFiles: API rewrites run before filesystem/trailing-slash logic to avoid redirect loops.
      // The :path* capture does NOT include the trailing slash, so we must append / in the destination
      // to satisfy Django's APPEND_SLASH and prevent 301 redirect chains.
      beforeFiles: [
        {
          source: "/api/:path*",
          destination: `${apiServerUrl.replace(/\/$/, "")}/api/:path*/`,
        },
      ],
    };
  },
};

export default nextConfig;
