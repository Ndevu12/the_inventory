import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Django expects trailing slashes. Without this, Next.js redirects /api/v1/x/ → /api/v1/x,
  // then Django redirects back → /api/v1/x/ → endless loop (ERR_TOO_MANY_REDIRECTS).
  trailingSlash: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
