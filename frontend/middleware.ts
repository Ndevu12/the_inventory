import createMiddleware from "next-intl/middleware";
import { type NextRequest, NextResponse } from "next/server";

import {
  JWT_ACCESS_COOKIE_NAME,
  parseLocalePath,
  requiresJwtAccessCookie,
} from "./src/lib/auth-paths";
import { routing } from "./src/i18n/routing";

const intlMiddleware = createMiddleware(routing);

function hasNonEmptyAccessCookie(request: NextRequest): boolean {
  const v = request.cookies.get(JWT_ACCESS_COOKIE_NAME)?.value;
  return typeof v === "string" && v.length > 0;
}

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  const { locale, innerPath } = parseLocalePath(request.nextUrl.pathname);
  if (
    requiresJwtAccessCookie(innerPath) &&
    !hasNonEmptyAccessCookie(request)
  ) {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}/login`;
    return NextResponse.redirect(url);
  }

  return intlMiddleware(request);
}

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
