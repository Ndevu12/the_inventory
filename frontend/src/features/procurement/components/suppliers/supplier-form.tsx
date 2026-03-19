"use client"

import type { UseFormReturn } from "react-hook-form"
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
import { PAYMENT_TERMS_OPTIONS } from "../../helpers/procurement-constants"
import type { CreateSupplierFormValues } from "../../helpers/supplier-schemas"

interface SupplierFormProps {
  form: UseFormReturn<CreateSupplierFormValues>
}

export function SupplierForm({ form }: SupplierFormProps) {
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
          Code <span className="text-destructive">*</span>
        </Label>
        <Input
          id="code"
          placeholder="e.g. SUP-001"
          aria-invalid={!!errors.code}
          {...register("code")}
        />
        {errors.code && (
          <p className="text-sm text-destructive">{errors.code.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">
          Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          placeholder="Company name"
          aria-invalid={!!errors.name}
          {...register("name")}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="contact_name">Contact Name</Label>
        <Input
          id="contact_name"
          placeholder="Contact person"
          {...register("contact_name")}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="email@example.com"
          aria-invalid={!!errors.email}
          {...register("email")}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone">Phone</Label>
        <Input
          id="phone"
          placeholder="+1 (555) 000-0000"
          {...register("phone")}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="lead_time_days">Lead Time (days)</Label>
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
        <Label htmlFor="payment_terms">Payment Terms</Label>
        <Select
          value={paymentTerms}
          onValueChange={(val) =>
            setValue("payment_terms", val as CreateSupplierFormValues["payment_terms"], {
              shouldValidate: true,
            })
          }
        >
          <SelectTrigger id="payment_terms" className="w-full">
            <SelectValue placeholder="Select terms" />
          </SelectTrigger>
          <SelectContent>
            {PAYMENT_TERMS_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="sm:col-span-2 space-y-2">
        <Label htmlFor="address">Address</Label>
        <Textarea
          id="address"
          placeholder="Street address, city, state, zip"
          {...register("address")}
        />
      </div>

      <div className="sm:col-span-2 space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Textarea
          id="notes"
          placeholder="Internal notes about this supplier"
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
          Active
        </Label>
      </div>
    </div>
  )
}
