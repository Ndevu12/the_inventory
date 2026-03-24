"use client"

import * as React from "react"
import { use } from "react"
import { useRouter } from "@/i18n/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useTranslations } from "next-intl"
import { toast } from "sonner"
import { Link } from "@/i18n/navigation"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { PageHeader } from "@/components/layout/page-header"
import type { ApiError } from "@/types/api-common"
import { useCustomer, useUpdateCustomer } from "../hooks/use-customers"
import {
  buildCreateCustomerSchema,
  type EditCustomerFormValues,
} from "../helpers/customer-schemas"
import { CustomerForm } from "../components/customers/customer-form"

interface CustomerEditPageProps {
  params: Promise<{ id: string }>
}

export function CustomerEditPage({ params }: CustomerEditPageProps) {
  const { id } = use(params)
  const customerId = Number(id)
  const router = useRouter()
  const t = useTranslations("Sales.customers.edit")
  const tVal = useTranslations("Sales.customers.validation")
  const tCommon = useTranslations("Common.actions")
  const { data: customer, isLoading } = useCustomer(customerId)
  const updateMutation = useUpdateCustomer()

  const customerSchema = React.useMemo(
    () =>
      buildCreateCustomerSchema({
        nameRequired: tVal("nameRequired"),
        emailInvalid: tVal("emailInvalid"),
      }),
    [tVal],
  )

  const form = useForm<EditCustomerFormValues>({
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

  React.useEffect(() => {
    if (customer) {
      form.reset({
        code: customer.code,
        name: customer.name,
        contact_name: customer.contact_name ?? "",
        email: customer.email ?? "",
        phone: customer.phone ?? "",
        address: customer.address ?? "",
        is_active: customer.is_active,
        notes: customer.notes ?? "",
      })
    }
  }, [customer, form])

  function onSubmit(values: EditCustomerFormValues) {
    updateMutation.mutate(
      { id: customerId, payload: values },
      {
        onSuccess: () => {
          toast.success(t("toastUpdated", { name: values.name }))
          router.push("/sales/customers")
        },
        onError: (error: unknown) => {
          const e = error as unknown as ApiError
          toast.error(e.message || t("toastUpdateFailed"))
        },
      },
    )
  }

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col gap-6 p-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-96 w-full rounded-xl" />
      </div>
    )
  }

  if (!customer) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-6">
        <p className="text-muted-foreground">{t("notFound")}</p>
        <Button variant="outline" render={<Link href="/sales/customers" />}>
          {t("backToList")}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={t("title", { name: customer.name })}
        description={t("description")}
      />

      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Card>
          <CardContent className="pt-6">
            <CustomerForm form={form} />
          </CardContent>
          <CardFooter className="flex justify-end gap-2">
            <Button variant="outline" render={<Link href="/sales/customers" />}>
              {tCommon("cancel")}
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? t("saving") : t("submit")}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}
