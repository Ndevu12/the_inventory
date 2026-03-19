import type { SubscriptionPlan, SubscriptionStatus, TenantRole } from "../types/settings.types"

export const ROLE_OPTIONS: { value: TenantRole; label: string }[] = [
  { value: "owner", label: "Owner" },
  { value: "admin", label: "Admin" },
  { value: "manager", label: "Manager" },
  { value: "viewer", label: "Viewer" },
]

export const ROLE_MAP: Record<TenantRole, string> = Object.fromEntries(
  ROLE_OPTIONS.map((o) => [o.value, o.label])
) as Record<TenantRole, string>

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

export const SUBSCRIPTION_PLAN_OPTIONS: { value: SubscriptionPlan; label: string }[] = [
  { value: "free", label: "Free" },
  { value: "starter", label: "Starter" },
  { value: "professional", label: "Professional" },
  { value: "enterprise", label: "Enterprise" },
]

export const SUBSCRIPTION_STATUS_OPTIONS: { value: SubscriptionStatus; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "trial", label: "Trial" },
  { value: "past_due", label: "Past Due" },
  { value: "cancelled", label: "Cancelled" },
  { value: "suspended", label: "Suspended" },
]

export const SUBSCRIPTION_PLAN_MAP: Record<SubscriptionPlan, string> = Object.fromEntries(
  SUBSCRIPTION_PLAN_OPTIONS.map((o) => [o.value, o.label])
) as Record<SubscriptionPlan, string>

export const SUBSCRIPTION_STATUS_MAP: Record<SubscriptionStatus, string> = Object.fromEntries(
  SUBSCRIPTION_STATUS_OPTIONS.map((o) => [o.value, o.label])
) as Record<SubscriptionStatus, string>
