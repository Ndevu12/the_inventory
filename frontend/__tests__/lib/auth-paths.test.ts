import { describe, expect, it } from "vitest";

import {
  isPublicAuthPath,
  parseLocalePath,
  requiresJwtAccessCookie,
} from "@/lib/auth-paths";

describe("auth-paths", () => {
  it("parseLocalePath strips known locale prefix", () => {
    expect(parseLocalePath("/en/login")).toEqual({
      locale: "en",
      innerPath: "/login",
    });
    expect(parseLocalePath("/fr")).toEqual({ locale: "fr", innerPath: "/" });
    expect(parseLocalePath("/")).toEqual({
      locale: "en",
      innerPath: "/",
    });
  });

  it("parseLocalePath treats unknown first segment as locale-free path", () => {
    expect(parseLocalePath("/login")).toEqual({
      locale: "en",
      innerPath: "/login",
    });
  });

  it("isPublicAuthPath covers auth and invitation flows", () => {
    expect(isPublicAuthPath("/login")).toBe(true);
    expect(isPublicAuthPath("/register")).toBe(true);
    expect(isPublicAuthPath("/no-organization")).toBe(true);
    expect(isPublicAuthPath("/accept-invitation")).toBe(true);
    expect(isPublicAuthPath("/accept-invitation/abc")).toBe(true);
    expect(isPublicAuthPath("/login/")).toBe(true);
  });

  it("requiresJwtAccessCookie is the complement on dashboard paths", () => {
    expect(requiresJwtAccessCookie("/")).toBe(true);
    expect(requiresJwtAccessCookie("/products")).toBe(true);
    expect(requiresJwtAccessCookie("/login")).toBe(false);
  });
});
