"use client"

import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { PageHeader } from "@/components/layout/page-header"
import { useTenant, useUpdateTenant } from "../hooks/use-settings"
import {
  createTenantProfileSchema,
  type TenantProfileFormValues,
} from "../helpers/tenant-schemas"
import { TenantProfileForm } from "../components/tenant-profile-form"
import { SubscriptionInfoCard } from "../components/subscription-info-card"

export function TenantSettingsPage() {
  const t = useTranslations("SettingsTenant.tenant")
  const tVal = useTranslations("SettingsTenant.tenant.validation")

  const tenantProfileSchema = React.useMemo(
    () =>
      createTenantProfileSchema({
        nameRequired: tVal("nameRequired"),
        hexColor: tVal("hexColor"),
      }),
    [tVal],
  )

  const { data: tenant, isLoading } = useTenant()
  const updateMutation = useUpdateTenant()

  const form = useForm<TenantProfileFormValues>({
    resolver: zodResolver(tenantProfileSchema),
    defaultValues: {
      name: "",
      branding_site_name: "",
      branding_primary_color: "",
    },
  })

  React.useEffect(() => {
    if (tenant) {
      form.reset({
        name: tenant.name,
        branding_site_name: tenant.branding_site_name ?? "",
        branding_primary_color: tenant.branding_primary_color ?? "",
      })
    }
  }, [tenant, form])

  function onSubmit(values: TenantProfileFormValues) {
    updateMutation.mutate(values, {
      onSuccess: () => {
        toast.success(t("toast.updated"))
      },
      onError: () => {
        toast.error(t("toast.updateFailed"))
      },
    })
  }

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col gap-6 p-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-64 rounded-xl lg:col-span-2" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    )
  }

  if (!tenant) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-6">
        <p className="text-muted-foreground">{t("loadError")}</p>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={t("page.title")}
        description={t("page.description")}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t("profile.title")}</CardTitle>
              <CardDescription>{t("profile.description")}</CardDescription>
            </CardHeader>
            <CardContent>
              <TenantProfileForm form={form} />
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  if (tenant) {
                    form.reset({
                      name: tenant.name,
                      branding_site_name: tenant.branding_site_name ?? "",
                      branding_primary_color:
                        tenant.branding_primary_color ?? "",
                    })
                  }
                }}
              >
                {t("reset")}
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? t("saving") : t("save")}
              </Button>
            </CardFooter>
          </Card>
        </form>

        <SubscriptionInfoCard tenant={tenant} />
      </div>
    </div>
  )
}
