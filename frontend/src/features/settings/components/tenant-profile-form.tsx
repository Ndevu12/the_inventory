"use client"

import * as React from "react"
import type { UseFormReturn } from "react-hook-form"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { TenantProfileFormValues } from "../helpers/tenant-schemas"

interface TenantProfileFormProps {
  form: UseFormReturn<TenantProfileFormValues>
}

export function TenantProfileForm({ form }: TenantProfileFormProps) {
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
          Tenant Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          placeholder="My Organisation"
          aria-invalid={!!errors.name}
          {...register("name")}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="branding_site_name">Site Name</Label>
        <Input
          id="branding_site_name"
          placeholder="Inventory Portal"
          {...register("branding_site_name")}
        />
        {errors.branding_site_name && (
          <p className="text-sm text-destructive">
            {errors.branding_site_name.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="branding_primary_color">Primary Color</Label>
        <div className="flex items-center gap-3">
          <Input
            id="branding_primary_color"
            placeholder="#3B82F6"
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
            aria-label="Pick primary color"
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
