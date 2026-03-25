import { apiClient } from "@/lib/api-client";
import type {
  LoginRequest,
  LoginResponse,
  MeResponse,
  ChangePasswordRequest,
  ChangePasswordResponse,
  AuthConfigResponse,
  RegisterRequest,
  RegisterResponse,
  ImpersonateStartResponse,
  UpdateProfileRequest,
} from "../types/auth.types";
import type { User } from "@/lib/auth-store";

const AUTH_BASE = "/auth";

export function fetchAuthConfig(): Promise<AuthConfigResponse> {
  return apiClient.get<AuthConfigResponse>(`${AUTH_BASE}/config/`);
}

export function login(credentials: LoginRequest): Promise<LoginResponse> {
  return apiClient.post<LoginResponse>(`${AUTH_BASE}/login/`, credentials);
}

export function register(payload: RegisterRequest): Promise<RegisterResponse> {
  return apiClient.post<RegisterResponse>(`${AUTH_BASE}/register/`, payload);
}

export function logout(): Promise<{ detail: string }> {
  return apiClient.post<{ detail: string }>(`${AUTH_BASE}/logout/`);
}

export function fetchMe(): Promise<MeResponse> {
  return apiClient.get<MeResponse>(`${AUTH_BASE}/me/`);
}

export function updateProfile(data: UpdateProfileRequest): Promise<User> {
  return apiClient.patch<User>(`${AUTH_BASE}/me/`, data);
}

export function changePassword(
  data: ChangePasswordRequest,
): Promise<ChangePasswordResponse> {
  return apiClient.post<ChangePasswordResponse>(
    `${AUTH_BASE}/change-password/`,
    data,
  );
}

export function impersonateStart(
  userId: number,
): Promise<ImpersonateStartResponse> {
  return apiClient.post<ImpersonateStartResponse>(
    `${AUTH_BASE}/impersonate/start/`,
    { user_id: userId },
  );
}

export function impersonateEnd(): Promise<{ detail: string }> {
  return apiClient.post<{ detail: string }>(`${AUTH_BASE}/impersonate/end/`);
}
