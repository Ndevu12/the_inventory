"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@/i18n/navigation";
import { toast } from "sonner";

import { useAuthStore } from "@/lib/auth-store";
import * as authApi from "../api/auth-api";
import { isTokenExpired } from "../helpers/auth-utils";
import type {
  LoginRequest,
  ChangePasswordRequest,
  MeResponse,
  RegisterRequest,
} from "../types/auth.types";

export const authKeys = {
  me: ["auth", "me"] as const,
  config: ["auth", "config"] as const,
};

/** Keep Zustand in sync with GET /auth/me/ (shared by all observers on `authKeys.me`). */
function syncMeResponseToStore(data: MeResponse): void {
  const { setUser, setTenant, setMemberships } = useAuthStore.getState();
  setUser(data.user);
  if (data.tenant) {
    setTenant(data.tenant.slug);
  }
  setMemberships(data.memberships ?? []);
}

async function fetchMeAndSyncStore(): Promise<MeResponse> {
  const data = await authApi.fetchMe();
  syncMeResponseToStore(data);
  return data;
}

export function useLogin() {
  const { setTokens, setUser, setTenant, setMemberships } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
      setUser(data.user);
      if (data.tenant) {
        setTenant(data.tenant.slug);
      }
      setMemberships(data.memberships ?? []);
      // Clear any stale auth/me error from previous session before navigating.
      queryClient.removeQueries({ queryKey: authKeys.me });
      // Defer navigation so store updates fully propagate before dashboard mounts.
      // Prevents race where AuthGuard reads stale/empty state and redirects back to login.
      setTimeout(() => router.replace("/"), 100);
    },
    onError: () => {
      toast.error("Invalid username or password");
    },
  });
}

export function useMe(enabled = true) {
  const { accessToken } = useAuthStore();

  return useQuery({
    queryKey: authKeys.me,
    queryFn: fetchMeAndSyncStore,
    enabled: enabled && !!accessToken && !isTokenExpired(accessToken),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useBootstrapAuth() {
  const { accessToken, refreshToken } = useAuthStore();
  // Run whenever we have tokens - refreshes user/tenant/memberships (e.g. after reload).
  // Must use the same queryFn as useMe() so TenantLocaleSync (mounted earlier) does not
  // steal the fetch and leave memberships unset in Zustand.
  const hasToken = !!accessToken || !!refreshToken;

  return useQuery({
    queryKey: authKeys.me,
    queryFn: fetchMeAndSyncStore,
    enabled: hasToken,
    staleTime: 5 * 60 * 1000,
    retry: 2, // Retry transient failures (network, 5xx) before giving up
  });
}

export function useLogout() {
  const { logout } = useAuthStore();
  const queryClient = useQueryClient();
  const router = useRouter();

  return () => {
    logout();
    queryClient.clear();
    router.push("/login");
  };
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: ChangePasswordRequest) => authApi.changePassword(data),
    onSuccess: () => {
      toast.success("Password updated successfully");
    },
    onError: () => {
      toast.error("Failed to change password. Please check your current password.");
    },
  });
}

export function useAuthConfig() {
  return useQuery({
    queryKey: authKeys.config,
    queryFn: authApi.fetchAuthConfig,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useImpersonate() {
  const {
    setTokens,
    setUser,
    setTenant,
    setMemberships,
    setImpersonation,
  } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: number) => authApi.impersonateStart(userId),
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
      setUser(data.user);
      if (data.tenant) {
        setTenant(data.tenant.slug);
      }
      setMemberships(data.memberships ?? []);
      setImpersonation({
        real_user: data.impersonation.real_user,
        real_access_token: data.impersonation.real_access_token,
        real_refresh_token: data.impersonation.real_refresh_token,
      });
      queryClient.clear();
      router.replace("/");
    },
    onError: () => {
      toast.error("Failed to start impersonation");
    },
  });
}

export function useExitImpersonation() {
  const { exitImpersonation } = useAuthStore();
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: () => authApi.impersonateEnd(),
    onSuccess: () => {
      exitImpersonation();
      queryClient.clear();
      router.replace("/");
    },
    onError: () => {
      toast.error("Failed to exit impersonation");
    },
  });
}

export function useRegister() {
  const { setTokens, setUser, setTenant, setMemberships } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: RegisterRequest) => authApi.register(payload),
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
      setUser(data.user);
      setTenant(data.tenant.slug);
      setMemberships(data.memberships);
      queryClient.removeQueries({ queryKey: authKeys.me });
      toast.success(`Welcome! Your organization ${data.tenant.name} has been created.`);
      router.replace("/");
    },
    onError: (error) => {
      toast.error(
        (error as { message?: string }).message ?? "Registration failed"
      );
    },
  });
}
