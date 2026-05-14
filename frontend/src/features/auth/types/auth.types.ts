import type { User, TenantInfo, Membership } from "@/lib/auth-store";

export type { User, TenantInfo, Membership };

export interface AuthConfigResponse {
  allow_registration: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access?: string;
  refresh?: string;
  user: User;
  tenant: TenantInfo | null;
  memberships?: Membership[];
}

export interface RefreshRequest {
  refresh: string;
}

export interface RefreshResponse {
  access: string;
  refresh?: string;
}

export interface MeResponse {
  user: User;
  tenant: TenantInfo | null;
  memberships: Membership[];
}

/** Body for PATCH /auth/me/ (partial updates allowed). */
export interface UpdateProfileRequest {
  email?: string;
  first_name?: string;
  last_name?: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  detail: string;
}

export interface RegisterRequest {
  organization_name: string;
  organization_slug?: string;
  owner_username: string;
  owner_email: string;
  owner_password: string;
  owner_first_name?: string;
  owner_last_name?: string;
}

export interface RegisterResponse {
  access?: string;
  refresh?: string;
  user: User;
  tenant: TenantInfo;
  memberships: Membership[];
}

export interface ImpersonateStartResponse {
  access?: string;
  refresh?: string;
  user: User;
  tenant: TenantInfo | null;
  memberships: Membership[];
  impersonation: {
    real_user: User;
  };
}
