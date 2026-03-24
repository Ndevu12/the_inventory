"use client"

import * as React from "react"
import { useRouter } from "@/i18n/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { Link } from "@/i18n/navigation"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { PageHeader } from "@/components/layout/page-header"
import { useCreateSupplier } from "../hooks/use-suppliers"
import {
  buildCreateSupplierSchema,
  type CreateSupplierFormValues,
} from "../helpers/supplier-schemas"
import { SupplierForm } from "../components/suppliers/supplier-form"

export function SupplierCreatePage() {
  const router = useRouter()
  const t = useTranslations("Procurement.suppliers.create")
  const tVal = useTranslations("Procurement.suppliers.validation")
  const tCommon = useTranslations("Common.actions")
  const createMutation = useCreateSupplier()

  const supplierSchema = React.useMemo(
    () =>
      buildCreateSupplierSchema({
        codeRequired: tVal("codeRequired"),
        nameRequired: tVal("nameRequired"),
        emailInvalid: tVal("emailInvalid"),
        leadTimeMin: tVal("leadTimeMin"),
      }),
    [tVal],
  )

  const form = useForm<CreateSupplierFormValues>({
    resolver: zodResolver(supplierSchema),
    defaultValues: {
      code: "",
      name: "",
      contact_name: "",
      email: "",
      phone: "",
      address: "",
      lead_time_days: 0,
      payment_terms: "net_30",
      is_active: true,
      notes: "",
    },
  })

  function onSubmit(values: CreateSupplierFormValues) {
    createMutation.mutate(values, {
      onSuccess: (supplier) => {
        toast.success(t("toastCreated", { name: supplier.name }))
        router.push("/procurement/suppliers")
      },
      onError: () => {
        toast.error(t("toastCreateFailed"))
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />

      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Card>
          <CardContent className="pt-6">
            <SupplierForm form={form} />
          </CardContent>
          <CardFooter className="flex justify-end gap-2">
            <Button variant="outline" render={<Link href="/procurement/suppliers" />}>
              {tCommon("cancel")}
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? t("creating") : t("submit")}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}
