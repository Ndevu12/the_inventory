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
import type { ApiError } from "@/types/api-common"
import { useCreateCustomer } from "../hooks/use-customers"
import {
  buildCreateCustomerSchema,
  type CreateCustomerFormValues,
} from "../helpers/customer-schemas"
import { CustomerForm } from "../components/customers/customer-form"
import type { CustomerCreatePayload } from "../types/sales.types"

export function CustomerCreatePage() {
  const router = useRouter()
  const t = useTranslations("Sales.customers.create")
  const tVal = useTranslations("Sales.customers.validation")
  const tCommon = useTranslations("Common.actions")
  const createMutation = useCreateCustomer()

  const customerSchema = React.useMemo(
    () =>
      buildCreateCustomerSchema({
        nameRequired: tVal("nameRequired"),
        emailInvalid: tVal("emailInvalid"),
      }),
    [tVal],
  )

  const form = useForm<CreateCustomerFormValues>({
    resolver: zodResolver(customerSchema),
    defaultValues: {
      code: "",
      name: "",
      contact_name: "",
      email: "",
      phone: "",
      address: "",
      is_active: true,
      notes: "",
    },
  })

  function onSubmit(values: CreateCustomerFormValues) {
    const { code, ...rest } = values
    const trimmedCode = code.trim()
    const payload: CustomerCreatePayload = {
      ...rest,
      ...(trimmedCode ? { code: trimmedCode } : {}),
    }
    createMutation.mutate(payload, {
      onSuccess: (customer) => {
        toast.success(t("toastCreated", { name: customer.name }))
        router.push("/sales/customers")
      },
      onError: (error: unknown) => {
        const e = error as unknown as ApiError
        toast.error(e.message || t("toastCreateFailed"))
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />

      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Card>
          <CardContent className="pt-6">
            <CustomerForm form={form} />
          </CardContent>
          <CardFooter className="flex justify-end gap-2">
            <Button variant="outline" render={<Link href="/sales/customers" />}>
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
