"use client"

import { useTranslations } from "next-intl"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import type { Tenant, SubscriptionPlan, SubscriptionStatus } from "../types/settings.types"

const STATUS_VARIANT: Record<
  SubscriptionStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  active: "default",
  trial: "secondary",
  past_due: "destructive",
  cancelled: "destructive",
  suspended: "destructive",
}

interface SubscriptionInfoCardProps {
  tenant: Tenant
}

function UsageRow({
  label,
  current,
  max,
}: {
  label: string
  current: number
  max: number
}) {
  const pct = max > 0 ? Math.round((current / max) * 100) : 0

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">
          {current} / {max}
        </span>
      </div>
      <Progress value={pct} className="h-2" />
    </div>
  )
}

export function SubscriptionInfoCard({ tenant }: SubscriptionInfoCardProps) {
  const t = useTranslations("SettingsTenant.subscription")
  const tPlans = useTranslations("SettingsTenant.plans")
  const tStatus = useTranslations("SettingsTenant.subscriptionStatus")

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{t("planLabel")}</p>
            <p className="text-xl font-semibold">
              {tPlans(tenant.subscription_plan as SubscriptionPlan)}
            </p>
          </div>
          <Badge variant={STATUS_VARIANT[tenant.subscription_status]}>
            {tStatus(tenant.subscription_status as SubscriptionStatus)}
          </Badge>
        </div>

        <div className="space-y-4">
          <UsageRow
            label={t("usageUsers")}
            current={tenant.user_count}
            max={tenant.max_users}
          />
          <UsageRow
            label={t("usageProducts")}
            current={tenant.product_count}
            max={tenant.max_products}
          />
        </div>
      </CardContent>
    </Card>
  )
}
