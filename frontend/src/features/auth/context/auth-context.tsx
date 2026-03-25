"use client";

import { useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { useAuthStore } from "@/lib/auth-store";
import type { User, Membership } from "@/lib/auth-store";

import { authKeys } from "../auth-query-keys";
import type { MeResponse } from "../types/auth.types";
import { syncMeResponseToStore } from "../lib/sync-me-to-store";

interface AuthContextValue {
  /** True after Zustand persist rehydration and optional RSC `/auth/me/` merge. */
  isReady: boolean;
  user: User | null;
  tenantSlug: string | null;
  memberships: Membership[];
  /** True when we have an authenticated user from server bootstrap. */
  isAuthenticated: boolean;
  /** True when viewing as another user (superuser impersonation). */
  isImpersonating: boolean;
  /** Call to log out and redirect to login. Clears store + query cache. */
  logout: () => void;
  /** Refetch `/auth/me/` (credentials + automatic refresh on 401 via apiClient). */
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
  /**
   * RSC bootstrap from GET /auth/me/ (cookies forwarded). `undefined` = skip server snapshot (e.g. tests).
   * `null` = no session or failed verify — overrides stale persisted user after rehydrate.
   */
  serverBootstrap?: MeResponse | null;
}

/**
 * AuthProvider gates UI until Zustand persist has rehydrated, then applies the optional RSC
 * `serverBootstrap` so HttpOnly-cookie truth wins over short-lived persisted user snapshot.
 */
export function AuthProvider({
  children,
  serverBootstrap,
}: AuthProviderProps) {
  /** Bumped after rehydration + optional RSC merge so `isReady` does not flicker. */
  const [readyNonce, setReadyNonce] = useState(0);
  const queryClient = useQueryClient();
  const serverBootstrapRef = useRef(serverBootstrap);
  serverBootstrapRef.current = serverBootstrap;

  const serverBootstrapDigest = useMemo(() => {
    if (serverBootstrap === undefined) {
      return "__omit__";
    }
    if (serverBootstrap === null) {
      return "__null__";
    }
    return JSON.stringify(serverBootstrap);
  }, [serverBootstrap]);

  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const user = useAuthStore((s) => s.user);
  const tenantSlug = useAuthStore((s) => s.tenantSlug);
  const memberships = useAuthStore((s) => s.memberships);
  const isImpersonating = useAuthStore((s) => s.isImpersonating());
  const storeLogout = useAuthStore((s) => s.logout);

  const isAuthenticated = !!user;

  const logout = useCallback(() => {
    storeLogout();
  }, [storeLogout]);

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: authKeys.me });
  }, [queryClient]);

  useEffect(() => {
    if (typeof window === "undefined" || !hasHydrated) {
      return;
    }

    const b = serverBootstrapRef.current;
    if (b !== undefined) {
      if (b) {
        syncMeResponseToStore(b);
      } else {
        useAuthStore.getState().logout();
      }
    }

    queueMicrotask(() => {
      setReadyNonce((n) => n + 1);
    });
  }, [hasHydrated, serverBootstrapDigest]);

  const isReady = hasHydrated && readyNonce > 0;

  const value: AuthContextValue = {
    isReady,
    user,
    tenantSlug,
    memberships,
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
