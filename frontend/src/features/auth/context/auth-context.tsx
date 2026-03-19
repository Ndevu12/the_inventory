"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { useAuthStore } from "@/lib/auth-store";
import { isTokenExpired } from "../helpers/auth-utils";
import type { User, Membership } from "@/lib/auth-store";

interface AuthContextValue {
  /** True only after client mount + persist rehydration. Gates all auth-dependent UI. */
  isReady: boolean;
  user: User | null;
  tenantSlug: string | null;
  memberships: Membership[];
  accessToken: string | null;
  /** True when we have a valid (non-expired) access token. */
  isAuthenticated: boolean;
  /** True when viewing as another user (superuser impersonation). */
  isImpersonating: boolean;
  /** Call to log out and redirect to login. Clears store + query cache. */
  logout: () => void;
  /** Force a re-check of auth state (used after login/register). */
  invalidate: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * AuthProvider gates rendering until auth state is ready (client-mounted + Zustand persist rehydrated).
 * This prevents hydration mismatches and redirect loops by never rendering auth-dependent UI
 * until we know the true auth state from localStorage.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [isReady, setIsReady] = useState(false);
  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const tenantSlug = useAuthStore((s) => s.tenantSlug);
  const memberships = useAuthStore((s) => s.memberships);
  const isImpersonating = useAuthStore((s) => s.isImpersonating());
  const storeLogout = useAuthStore((s) => s.logout);

  const isAuthenticated =
    !!accessToken && !isTokenExpired(accessToken);

  const logout = useCallback(() => {
    storeLogout();
  }, [storeLogout]);

  const invalidate = useCallback(() => {
    // No-op for now; store updates are synchronous. Kept for API consistency.
  }, []);

  // Wait for client mount + Zustand persist rehydration. Never render auth UI until ready.
  useEffect(() => {
    if (typeof window === "undefined") return;

    if (hasHydrated) {
      setIsReady(true);
      return;
    }

    // Persist rehydration is async. Poll until _hasHydrated or max 1s.
    const id = setInterval(() => {
      if (useAuthStore.getState()._hasHydrated) {
        setIsReady(true);
      }
    }, 50);
    const timeout = setTimeout(() => {
      clearInterval(id);
      setIsReady(true);
    }, 1000);
    return () => {
      clearInterval(id);
      clearTimeout(timeout);
    };
  }, [hasHydrated]);

  const value: AuthContextValue = {
    isReady,
    user,
    tenantSlug,
    memberships,
    accessToken,
    isAuthenticated,
    isImpersonating,
    logout,
    invalidate,
  };

  // Block all auth-dependent UI until we know true state. Prevents hydration mismatch + redirect loops.
  if (!isReady) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <p className="text-sm text-muted-foreground">Loading…</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}
