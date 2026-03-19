import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for handling API requests.
 *
 * The actual rewriting of /api/* to the backend server (configured via API_SERVER_URL)
 * is handled by next.config.ts, not here.
 */
export function middleware(request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: ["/api/:path*"],
};
