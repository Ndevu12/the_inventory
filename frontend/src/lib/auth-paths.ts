import { DEFAULT_LOCALE, SUPPORTED_LOCALES } from "@/i18n/routing";

export const JWT_ACCESS_COOKIE_NAME = "access_token" as const;

/**
 * Path after locale segment (leading slash). Examples: `/`, `/login`, `/products`.
 * When the first segment is not a known locale, `innerPath` is the full pathname.
 */
export type ParsedLocalePath = {
  locale: string;
  innerPath: string;
};

/** Paths that do not require JWT access cookie (tenant UI); prefix is without locale. */
const PUBLIC_INNER_PATHS = new Set([
  "/login",
  "/register",
  "/no-organization",
]);

function normalizeInnerPath(segments: string[]): string {
  if (segments.length === 0) {
    return "/";
  }
  return `/${segments.join("/")}`;
}

/** Collapse trailing slashes so `/login/` matches public list. */
export function normalizeAuthInnerPath(innerPath: string): string {
  const trimmed = innerPath.trim();
  if (trimmed === "" || trimmed === "/") {
    return "/";
  }
  return trimmed.replace(/\/+$/, "") || "/";
}

/**
 * Split Next.js pathname into locale (for redirects) and inner app path for auth rules.
 */
export function parseLocalePath(pathname: string): ParsedLocalePath {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) {
    return { locale: DEFAULT_LOCALE, innerPath: "/" };
  }
  const [first, ...rest] = segments;
  if (SUPPORTED_LOCALES.includes(first)) {
    return {
      locale: first,
      innerPath: normalizeAuthInnerPath(normalizeInnerPath(rest)),
    };
  }
  return {
    locale: DEFAULT_LOCALE,
    innerPath: normalizeAuthInnerPath(pathname || "/"),
  };
}

/**
 * True when the route is allowed without `access_token` (login, register, invite, etc.).
 */
export function isPublicAuthPath(innerPath: string): boolean {
  const p = normalizeAuthInnerPath(innerPath);
  if (PUBLIC_INNER_PATHS.has(p)) {
    return true;
  }
  if (
    p === "/accept-invitation" ||
    p.startsWith("/accept-invitation/")
  ) {
    return true;
  }
  return false;
}

/**
 * Tenant dashboard and other authenticated UI (anything not public).
 */
export function requiresJwtAccessCookie(innerPath: string): boolean {
  return !isPublicAuthPath(innerPath);
}
