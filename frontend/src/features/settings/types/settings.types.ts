export type TenantRole = "owner" | "admin" | "manager" | "viewer"

export type SubscriptionPlan = "free" | "starter" | "professional" | "enterprise"

export type SubscriptionStatus = "active" | "trial" | "past_due" | "cancelled" | "suspended"

export interface Tenant {
  id: number
  name: string
  slug: string
  is_active: boolean
  branding_site_name: string
  branding_primary_color: string
  branding_logo: number | null
  subscription_plan: SubscriptionPlan
  subscription_status: SubscriptionStatus
  max_users: number
  max_products: number
  user_count: number
  product_count: number
  created_at: string
  updated_at: string
}

export interface TenantUpdatePayload {
  name?: string
  branding_site_name?: string
  branding_primary_color?: string
  branding_logo?: number | null
}

export interface TenantMember {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: TenantRole
  is_active: boolean
  is_default: boolean
  created_at: string
}

export interface MemberUpdatePayload {
  role?: TenantRole
  is_active?: boolean
}

export interface MemberListParams {
  page?: number
  page_size?: number
  search?: string
  ordering?: string
  role?: string
}

export type InvitationStatus = "pending" | "accepted" | "cancelled" | "expired"

export interface Invitation {
  id: number
  email: string
  role: TenantRole
  status: InvitationStatus
  token: string
  invited_by_username: string | null
  tenant_name: string
  created_at: string
  expires_at: string
  accepted_at: string | null
}

export interface InvitationCreatePayload {
  email: string
  role: TenantRole
}

export interface InvitationInfo {
  email: string
  role: string
  tenant_name: string
  expires_at: string
  status: string
  needs_account: boolean
}

export interface AcceptInvitationPayload {
  username?: string
  password?: string
  first_name?: string
  last_name?: string
}

// Platform users (superuser only)
export interface PlatformUserTenant {
  id: number
  name: string
  slug: string
  role?: string
  is_default?: boolean
  membership_id?: number
}

export interface PlatformUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  date_joined: string
  last_login?: string | null
  tenants_display: PlatformUserTenant[]
}

export interface PlatformUserListParams {
  page?: number
  page_size?: number
  search?: string
  ordering?: string
  is_active?: boolean
  is_staff?: boolean
  tenant?: number
}

export interface PlatformUserCreatePayload {
  username: string
  email: string
  password: string
  first_name?: string
  last_name?: string
  is_active?: boolean
  tenant_ids?: number[]
  default_role?: TenantRole
}

export interface PlatformUserUpdatePayload {
  email?: string
  first_name?: string
  last_name?: string
  is_active?: boolean
  is_staff?: boolean
}

export interface PlatformTenant {
  id: number
  name: string
  slug: string
}

// Platform invitation (superuser only) — extends Invitation with tenant_id
export interface PlatformInvitation {
  id: number
  email: string
  tenant_id: number
  tenant_name: string
  role: TenantRole
  status: InvitationStatus
  invited_by_username: string | null
  created_at: string
  expires_at: string
  accepted_at: string | null
}

export interface PlatformInvitationListParams {
  page?: number
  page_size?: number
  ordering?: string
  status?: InvitationStatus
  tenant?: number
  date_from?: string
  date_to?: string
}

export interface PlatformUserAssignTenantPayload {
  tenant_id: number
  role: TenantRole
  is_default?: boolean
}

// Platform billing (superuser only)
export interface BillingTenant {
  id: number
  name: string
  slug: string
  is_active: boolean
  subscription_plan: SubscriptionPlan
  subscription_status: SubscriptionStatus
  max_users: number
  max_products: number
  max_users_override: number | null
  max_products_override: number | null
  user_count: number
  product_count: number
  effective_max_users: number
  effective_max_products: number
  billing_notes: string
  created_at: string
  updated_at: string
}

export interface BillingTenantUpdatePayload {
  subscription_plan?: SubscriptionPlan
  subscription_status?: SubscriptionStatus
  max_users?: number
  max_products?: number
  max_users_override?: number | null
  max_products_override?: number | null
  billing_notes?: string
