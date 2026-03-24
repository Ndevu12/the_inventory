import type { SubscriptionPlan, SubscriptionStatus, TenantRole } from "../types/settings.types"

/** Role keys for selects and badges (labels come from i18n `SettingsTenant.roles.*`). */
export const TENANT_ROLE_VALUES: TenantRole[] = [
  "owner",
  "admin",
  "manager",
  "viewer",
]

export const ROLE_COLOR_MAP: Record<
  TenantRole,
  { bg: string; text: string }
> = {
  owner: {
    bg: "bg-purple-100 dark:bg-purple-900/30",
    text: "text-purple-800 dark:text-purple-300",
  },
  admin: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-800 dark:text-blue-300",
  },
  manager: {
    bg: "bg-amber-100 dark:bg-amber-900/30",
    text: "text-amber-800 dark:text-amber-300",
  },
  viewer: {
    bg: "bg-gray-100 dark:bg-gray-800/30",
    text: "text-gray-800 dark:text-gray-300",
  },
}

export const SUBSCRIPTION_PLAN_VALUES: SubscriptionPlan[] = [
  "free",
  "starter",
  "professional",
  "enterprise",
]

export const SUBSCRIPTION_STATUS_VALUES: SubscriptionStatus[] = [
  "active",
  "trial",
  "past_due",
  "cancelled",
  "suspended",
]
