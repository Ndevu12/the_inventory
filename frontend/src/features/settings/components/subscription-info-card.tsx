"use client"

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

const PLAN_LABELS: Record<SubscriptionPlan, string> = {
  free: "Free",
  starter: "Starter",
  professional: "Professional",
  enterprise: "Enterprise",
}

const STATUS_VARIANT: Record<SubscriptionStatus, "default" | "secondary" | "destructive" | "outline"> = {
  active: "default",
  trial: "secondary",
  past_due: "destructive",
  cancelled: "destructive",
  suspended: "destructive",
}

const STATUS_LABELS: Record<SubscriptionStatus, string> = {
  active: "Active",
  trial: "Trial",
  past_due: "Past Due",
  cancelled: "Cancelled",
  suspended: "Suspended",
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
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Subscription</CardTitle>
        <CardDescription>Your current plan and usage</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Plan</p>
            <p className="text-xl font-semibold">
              {PLAN_LABELS[tenant.subscription_plan]}
            </p>
          </div>
          <Badge variant={STATUS_VARIANT[tenant.subscription_status]}>
            {STATUS_LABELS[tenant.subscription_status]}
          </Badge>
        </div>

        <div className="space-y-4">
          <UsageRow
            label="Users"
            current={tenant.user_count}
            max={tenant.max_users}
          />
          <UsageRow
            label="Products"
            current={tenant.product_count}
            max={tenant.max_products}
          />
        </div>
      </CardContent>
    </Card>
  )
}
