"use client"

import type { UseFormReturn } from "react-hook-form"
import { useTranslations } from "next-intl"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { TenantProfileFormValues } from "../helpers/tenant-schemas"

interface TenantProfileFormProps {
  form: UseFormReturn<TenantProfileFormValues>
}

export function TenantProfileForm({ form }: TenantProfileFormProps) {
  const t = useTranslations("SettingsTenant.tenant.form")
  const {
    register,
    formState: { errors },
    watch,
    setValue,
  } = form

  const primaryColor = watch("branding_primary_color")

  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <div className="space-y-2">
        <Label htmlFor="name">
          {t("tenantName")}{" "}
          <span className="text-destructive" aria-hidden>
            *
          </span>
          <span className="sr-only">{t("requiredMarker")}</span>
        </Label>
        <Input
          id="name"
          placeholder={t("placeholderOrg")}
          aria-invalid={!!errors.name}
          {...register("name")}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="branding_site_name">{t("siteName")}</Label>
        <Input
          id="branding_site_name"
          placeholder={t("placeholderSite")}
          {...register("branding_site_name")}
        />
        {errors.branding_site_name && (
          <p className="text-sm text-destructive">
            {errors.branding_site_name.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="branding_primary_color">{t("primaryColor")}</Label>
        <div className="flex items-center gap-3">
          <Input
            id="branding_primary_color"
            placeholder={t("placeholderColor")}
            className="flex-1"
            aria-invalid={!!errors.branding_primary_color}
            {...register("branding_primary_color")}
          />
          <input
            type="color"
            value={primaryColor || "#3B82F6"}
            onChange={(e) =>
              setValue("branding_primary_color", e.target.value, {
                shouldValidate: true,
              })
            }
            className="h-9 w-9 shrink-0 cursor-pointer rounded border border-input p-0.5"
            aria-label={t("colorPickerAria")}
          />
        </div>
        {errors.branding_primary_color && (
          <p className="text-sm text-destructive">
            {errors.branding_primary_color.message}
          </p>
        )}
      </div>
    </div>
  )
}
