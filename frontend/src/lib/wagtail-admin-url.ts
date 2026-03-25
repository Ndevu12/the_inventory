/**
 * Path to the cross-tenant platform audit snippet list in Wagtail
 * (app-relative, trailing slash; matches SnippetViewSet for ComplianceAuditLog).
 */
export const PLATFORM_AUDIT_LOG_WAGTAIL_PATH =
  "/admin/snippets/inventory/complianceauditlog/" as const;

/**
 * Full URL to open Wagtail admin for the current deployment.
 * Uses the host from `NEXT_PUBLIC_API_URL` when it is absolute; otherwise the browser origin.
 */
export function getWagtailAdminBaseUrl(): string {
  const api = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";
  try {
    if (api.startsWith("http://") || api.startsWith("https://")) {
      return new URL(api).origin;
    }
  } catch {
    /* ignore invalid URL */
  }
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return "";
}

function snippetPathTrailingSlash(path: string): string {
  const t = path.replace(/\/+$/, "");
  return `${t}/`;
}

/** Full URL to the read-only platform audit snippet index (all tenants, all scopes). */
export function getWagtailPlatformAuditLogUrl(): string {
  const base = getWagtailAdminBaseUrl().replace(/\/$/, "");
  const path = snippetPathTrailingSlash(PLATFORM_AUDIT_LOG_WAGTAIL_PATH);
  return base ? `${base}${path}` : path;
}

/** Deep link to Wagtail inspect view for a single compliance audit log row (pk). */
export function getWagtailPlatformAuditLogInspectUrl(pk: number): string {
  const base = getWagtailAdminBaseUrl().replace(/\/$/, "");
  const list = snippetPathTrailingSlash(PLATFORM_AUDIT_LOG_WAGTAIL_PATH);
  const path = `${list}inspect/${pk}/`;
  return base ? `${base}${path}` : path;
}
