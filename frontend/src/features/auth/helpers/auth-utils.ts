interface JwtPayload {
  exp: number;
  iat: number;
  jti: string;
  user_id: number;
  token_type: string;
}

export function parseJwtPayload(token: string): JwtPayload | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1]));
    return payload as JwtPayload;
  } catch {
    return null;
  }
}

/**
 * Returns true if the token is expired or will expire within `bufferSeconds`.
 * Defaults to a 30-second buffer to avoid edge-case races.
 */
export function isTokenExpired(
  token: string | null,
  bufferSeconds = 30,
): boolean {
  if (!token) return true;
  const payload = parseJwtPayload(token);
  if (!payload?.exp) return true;
  const nowSeconds = Math.floor(Date.now() / 1000);
  return payload.exp - nowSeconds < bufferSeconds;
}
