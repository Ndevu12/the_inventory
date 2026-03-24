"use client"

import type { UseFormReturn } from "react-hook-form"
import { useTranslations } from "next-intl"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import type { CreateCustomerFormValues } from "../../helpers/customer-schemas"

interface CustomerFormProps {
  form: UseFormReturn<CreateCustomerFormValues>
}

export function CustomerForm({ form }: CustomerFormProps) {
  const t = useTranslations("Sales.customers.form")
  const tPh = useTranslations("Sales.customers.form.placeholders")
  const {
    register,
    formState: { errors },
    watch,
    setValue,
  } = form

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="code">{t("codeOptional")}</Label>
          <Input
            id="code"
            placeholder={tPh("code")}
            {...register("code")}
          />
          {errors.code && (
            <p className="text-xs text-destructive">{errors.code.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="name">{t("name")}</Label>
          <Input id="name" placeholder={tPh("name")} {...register("name")} />
          {errors.name && (
            <p className="text-xs text-destructive">{errors.name.message}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="contact_name">{t("contactPerson")}</Label>
          <Input
            id="contact_name"
            placeholder={tPh("contact")}
            {...register("contact_name")}
          />
          {errors.contact_name && (
            <p className="text-xs text-destructive">
              {errors.contact_name.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">{t("email")}</Label>
          <Input
            id="email"
            type="email"
            placeholder={tPh("email")}
            {...register("email")}
          />
          {errors.email && (
            <p className="text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="phone">{t("phone")}</Label>
          <Input id="phone" placeholder={tPh("phone")} {...register("phone")} />
          {errors.phone && (
            <p className="text-xs text-destructive">{errors.phone.message}</p>
          )}
        </div>

        <div className="flex items-center gap-3 pt-6">
          <Switch
            id="is_active"
            checked={watch("is_active")}
            onCheckedChange={(checked) => setValue("is_active", checked)}
          />
          <Label htmlFor="is_active">{t("active")}</Label>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="address">{t("address")}</Label>
        <Textarea
          id="address"
          rows={3}
          placeholder={tPh("address")}
          {...register("address")}
        />
        {errors.address && (
          <p className="text-xs text-destructive">{errors.address.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">{t("notes")}</Label>
        <Textarea
          id="notes"
          rows={3}
          placeholder={tPh("notes")}
          {...register("notes")}
        />
        {errors.notes && (
          <p className="text-xs text-destructive">{errors.notes.message}</p>
        )}
      </div>
    </div>
  )
}
