"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "@/i18n/navigation";
import { toast } from "sonner";

import { useAuthStore } from "@/lib/auth-store";
import * as authApi from "../api/auth-api";
import { useAuth } from "../context/auth-context";
import { authKeys } from "../auth-query-keys";
import { syncMeResponseToStore } from "../lib/sync-me-to-store";
import type {
  LoginRequest,
  ChangePasswordRequest,
  MeResponse,
  RegisterRequest,
  UpdateProfileRequest,
} from "../types/auth.types";
import type { ApiError } from "@/types/api-common";

export { authKeys };

async function fetchMeAndSyncStore(): Promise<MeResponse> {
  const data = await authApi.fetchMe();
  syncMeResponseToStore(data);
  return data;
}

export function useLogin() {
  const { invalidate } = useAuth();
  const { setUser, setTenant, setMemberships } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: (data) => {
      setUser(data.user);
      if (data.tenant) {
        setTenant(data.tenant.slug);
      }
      setMemberships(data.memberships ?? []);
      // Refetch `/auth/me/` so React Query drops stale errors and matches cookies + store.
      invalidate();
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
  return useQuery({
    queryKey: authKeys.me,
    queryFn: fetchMeAndSyncStore,
    enabled,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useBootstrapAuth() {
  return useQuery({
    queryKey: authKeys.me,
    queryFn: fetchMeAndSyncStore,
    enabled: true,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useLogout() {
  const { logout } = useAuthStore();
  const queryClient = useQueryClient();
  const router = useRouter();

  return () => {
    void authApi.logout().catch(() => {
      // Always clear client auth state even if logout API fails.
    });
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

export function useUpdateProfile() {
  const { invalidate } = useAuth();
  const { setUser } = useAuthStore();

  return useMutation({
    mutationFn: (data: UpdateProfileRequest) => authApi.updateProfile(data),
    onSuccess: (user) => {
      setUser(user);
      invalidate();
      toast.success("Profile updated");
    },
    onError: (error: unknown) => {
      const message =
        error &&
        typeof error === "object" &&
        "message" in error &&
        typeof (error as ApiError).message === "string"
          ? (error as ApiError).message
          : "Failed to update profile";
      toast.error(message);
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
      setUser(data.user);
      if (data.tenant) {
        setTenant(data.tenant.slug);
      }
      setMemberships(data.memberships ?? []);
      setImpersonation({
        real_user: data.impersonation.real_user,
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
  const { invalidate } = useAuth();
  const { setUser, setTenant, setMemberships } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: RegisterRequest) => authApi.register(payload),
    onSuccess: (data) => {
      setUser(data.user);
      setTenant(data.tenant.slug);
      setMemberships(data.memberships);
      invalidate();
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
