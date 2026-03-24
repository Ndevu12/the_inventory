"use client"

import type { UseFormReturn } from "react-hook-form"
import { useTranslations } from "next-intl"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  PAYMENT_TERMS_VALUES,
  paymentTermsLabel,
} from "../../helpers/procurement-constants"
import type { CreateSupplierFormValues } from "../../helpers/supplier-schemas"

interface SupplierFormProps {
  form: UseFormReturn<CreateSupplierFormValues>
}

export function SupplierForm({ form }: SupplierFormProps) {
  const t = useTranslations("Procurement.suppliers.form")
  const tPh = useTranslations("Procurement.suppliers.form.placeholders")
  const tPay = useTranslations("Procurement.paymentTerms")
  const {
    register,
    formState: { errors },
    setValue,
    watch,
  } = form

  const paymentTerms = watch("payment_terms")
  const isActive = watch("is_active")

  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <div className="space-y-2">
        <Label htmlFor="code">
          {t("code")} <span className="text-destructive">*</span>
        </Label>
        <Input
          id="code"
          placeholder={tPh("code")}
          aria-invalid={!!errors.code}
          {...register("code")}
        />
        {errors.code && (
          <p className="text-sm text-destructive">{errors.code.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">
          {t("name")} <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          placeholder={tPh("companyName")}
          aria-invalid={!!errors.name}
          {...register("name")}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="contact_name">{t("contactName")}</Label>
        <Input
          id="contact_name"
          placeholder={tPh("contactPerson")}
          {...register("contact_name")}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">{t("email")}</Label>
        <Input
          id="email"
          type="email"
          placeholder={tPh("email")}
          aria-invalid={!!errors.email}
          {...register("email")}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone">{t("phone")}</Label>
        <Input
          id="phone"
          placeholder={tPh("phone")}
          {...register("phone")}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="lead_time_days">{t("leadTimeDays")}</Label>
        <Input
          id="lead_time_days"
          type="number"
          min={0}
          aria-invalid={!!errors.lead_time_days}
          {...register("lead_time_days", { valueAsNumber: true })}
        />
        {errors.lead_time_days && (
          <p className="text-sm text-destructive">
            {errors.lead_time_days.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="payment_terms">{t("paymentTerms")}</Label>
        <Select
          value={paymentTerms}
          onValueChange={(val) =>
            setValue("payment_terms", val as CreateSupplierFormValues["payment_terms"], {
              shouldValidate: true,
            })
          }
        >
          <SelectTrigger id="payment_terms" className="w-full">
            <SelectValue placeholder={t("selectTerms")}>
              {(value: string | null) =>
                value ? paymentTermsLabel(value, (k) => tPay(k)) : null}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {PAYMENT_TERMS_VALUES.map((opt) => (
              <SelectItem key={opt} value={opt}>
                {tPay(opt)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="sm:col-span-2 space-y-2">
        <Label htmlFor="address">{t("address")}</Label>
        <Textarea
          id="address"
          placeholder={tPh("address")}
          {...register("address")}
        />
      </div>

      <div className="sm:col-span-2 space-y-2">
        <Label htmlFor="notes">{t("notes")}</Label>
        <Textarea
          id="notes"
          placeholder={tPh("notes")}
          {...register("notes")}
        />
      </div>

      <div className="sm:col-span-2 flex items-center gap-2">
        <Checkbox
          id="is_active"
          checked={isActive}
          onCheckedChange={(checked) =>
            setValue("is_active", checked === true, { shouldValidate: true })
          }
        />
        <Label htmlFor="is_active" className="cursor-pointer">
          {t("active")}
        </Label>
      </div>
    </div>
  )
}
