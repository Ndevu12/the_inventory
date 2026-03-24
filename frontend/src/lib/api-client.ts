import { useAuthStore } from "./auth-store";
import type { ApiError } from "@/types/api-common";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";

let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const { refreshToken, setTokens, logout } = useAuthStore.getState();
  if (!refreshToken) {
    logout();
    return false;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!res.ok) {
      logout();
      return false;
    }

    const data = await res.json();
    setTokens(data.access, data.refresh ?? refreshToken);
    return true;
  } catch {
    // Network error during refresh - don't logout. User stays on page with tokens.
    // They can retry or refresh. Only explicit 4xx from refresh endpoint triggers logout.
    return false;
  }
}

/**
 * Mutex-locked refresh: concurrent 401s share a single refresh attempt.
 */
function refreshWithMutex(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

function buildHeaders(custom?: HeadersInit): Headers {
  const headers = new Headers(custom);
  const { accessToken, tenantSlug } = useAuthStore.getState();

  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  if (tenantSlug) {
    headers.set("X-Tenant", tenantSlug);
  }

  return headers;
}

function buildUrl(path: string, params?: Record<string, string>): string {
  // Ensure trailing slash for Django's APPEND_SLASH (avoids POST redirect issues)
  const normalizedPath =
    !path.startsWith("http") &&
    !path.includes("?") &&
    path.length > 1 &&
    !path.endsWith("/")
      ? `${path}/`
      : path;
  const url = path.startsWith("http")
    ? path
    : `${API_BASE}${normalizedPath}`;
  if (!params) return url;
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    searchParams.set(key, String(value));
  }
  const qs = searchParams.toString();
  return qs ? `${url}?${qs}` : url;
}

/** Flatten DRF-style ``{ field: ["msg"], ... }`` bodies into one readable string. */
function drfErrorsToMessage(body: Record<string, unknown>): string | null {
  const parts: string[] = [];
  for (const [key, val] of Object.entries(body)) {
    if (key === "detail") continue;
    if (Array.isArray(val)) {
      const msgs = val.filter((x): x is string => typeof x === "string");
      if (msgs.length) {
        const prefix =
          key === "non_field_errors" ? "" : `${key.replace(/_/g, " ")}: `;
        parts.push(prefix + msgs.join(", "));
      }
    } else if (typeof val === "string" && val.trim()) {
      parts.push(`${key.replace(/_/g, " ")}: ${val}`);
    }
  }
  return parts.length ? parts.join(" · ") : null;
}

function drfErrorsRecord(
  body: Record<string, unknown>,
): Record<string, string[]> | undefined {
  const out: Record<string, string[]> = {};
  for (const [k, v] of Object.entries(body)) {
    if (k === "detail") continue;
    if (Array.isArray(v) && v.every((x) => typeof x === "string")) {
      out[k] = v as string[];
    }
  }
  return Object.keys(out).length ? out : undefined;
}

async function parseErrorResponse(res: Response): Promise<ApiError> {
  let body: Record<string, unknown> = {};
  try {
    body = await res.json();
  } catch {
    // non-JSON error body
  }

  const detailStr =
    typeof body.detail === "string" ? body.detail : undefined;
  const fieldMessage = drfErrorsToMessage(body);
  const message =
    detailStr ??
    fieldMessage ??
    `Request failed with status ${res.status}`;

  return {
    status: res.status,
    message,
    detail: detailStr,
    errors:
      (body.errors as Record<string, string[]> | undefined) ??
      drfErrorsRecord(body),
  };
}

async function request<T>(
  method: string,
  path: string,
  options: {
    body?: unknown;
    params?: Record<string, string>;
    headers?: HeadersInit;
  } = {},
): Promise<T> {
  const url = buildUrl(path, options.params);
  const headers = buildHeaders(options.headers);

  const init: RequestInit = { method, headers };

  if (options.body !== undefined) {
    if (options.body instanceof FormData) {
      headers.delete("Content-Type");
      init.body = options.body;
    } else {
      init.body = JSON.stringify(options.body);
    }
  }

  let res = await fetch(url, init);

  if (res.status === 401 && useAuthStore.getState().refreshToken) {
    const refreshed = await refreshWithMutex();
    if (refreshed) {
      const retryHeaders = buildHeaders(options.headers);
      if (options.body instanceof FormData) {
        retryHeaders.delete("Content-Type");
      }
      res = await fetch(url, { ...init, headers: retryHeaders });
    }
  }

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  get<T>(path: string, params?: Record<string, string>): Promise<T> {
    return request<T>("GET", path, { params });
  },

  post<T>(path: string, body?: unknown): Promise<T> {
    return request<T>("POST", path, { body });
  },

  patch<T>(path: string, body?: unknown): Promise<T> {
    return request<T>("PATCH", path, { body });
  },

  put<T>(path: string, body?: unknown): Promise<T> {
    return request<T>("PUT", path, { body });
  },

  delete(path: string): Promise<void> {
    return request<void>("DELETE", path);
  },

  upload<T>(path: string, formData: FormData): Promise<T> {
    return request<T>("POST", path, { body: formData });
  },
};
