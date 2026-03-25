import { headers } from "next/headers";

import type { MeResponse } from "@/features/auth/types/auth.types";

/**
 * Absolute API base for server-side fetch. Prefer `NEXT_PUBLIC_API_URL` when absolute;
 * otherwise same-origin relative path resolved against the incoming request host.
 */
export async function getServerApiBaseUrl(): Promise<string> {
  const env = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";
  const trimmed = env.replace(/\/$/, "");
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return trimmed;
  }
  const h = await headers();
  const host = h.get("x-forwarded-host") ?? h.get("host") ?? "localhost:3000";
  const proto = h.get("x-forwarded-proto") ?? "http";
  const path = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  return `${proto}://${host}${path}`;
}

/**
 * Forward browser cookies to Django for GET /auth/me/ during RSC render.
 */
export async function fetchAuthMeOnServer(
  cookieHeader: string,
  uiLocale: string,
): Promise<MeResponse | null> {
  if (!cookieHeader.trim()) {
    return null;
  }
  const base = await getServerApiBaseUrl();
  const url = `${base}/auth/me/?language=${encodeURIComponent(uiLocale)}`;
  const res = await fetch(url, {
    headers: {
      Cookie: cookieHeader,
      Accept: "application/json",
    },
    cache: "no-store",
  });
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as MeResponse;
}
