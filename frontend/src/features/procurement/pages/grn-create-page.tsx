"use client"

import * as React from "react"
import { useRouter } from "@/i18n/navigation"
import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useTranslations } from "next-intl"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { GRNForm } from "../components/grn/grn-form"
import { useCreateGRN, usePurchaseOrders, useGRNLocations } from "../hooks/use-grn"
import {
  buildCreateGRNSchema,
  type CreateGRNFormValues,
} from "../helpers/grn-schemas"

export function GRNCreatePage() {
  const router = useRouter()
  const t = useTranslations("Procurement.grn.create")
  const tVal = useTranslations("Procurement.grn.validation")
  const tCommon = useTranslations("Common.actions")
  const createMutation = useCreateGRN()
  const { data: poData, isLoading: posLoading } = usePurchaseOrders()
  const { data: locData, isLoading: locsLoading } = useGRNLocations()

  const purchaseOrders = poData?.results ?? []
  const locations = locData?.results ?? []

  const grnSchema = React.useMemo(
    () =>
      buildCreateGRNSchema({
        grnNumberRequired: tVal("grnNumberRequired"),
        purchaseOrderRequired: tVal("purchaseOrderRequired"),
        receivedDateRequired: tVal("receivedDateRequired"),
        locationRequired: tVal("locationRequired"),
      }),
    [tVal],
  )

  const form = useForm<CreateGRNFormValues>({
    resolver: zodResolver(grnSchema) as Resolver<CreateGRNFormValues>,
    defaultValues: {
      grn_number: "",
      purchase_order: undefined,
      received_date: new Date().toISOString().split("T")[0],
      location: undefined,
      notes: "",
    },
  })

  function onSubmit(values: CreateGRNFormValues) {
    createMutation.mutate(values, {
      onSuccess: (grn) => {
        toast.success(t("toastCreated", { grnNumber: grn.grn_number }))
        router.push("/procurement/goods-received")
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? t("toastError")
        toast.error(message)
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <GRNForm
          form={form}
          purchaseOrders={purchaseOrders}
          locations={locations}
          isLoadingPOs={posLoading}
          isLoadingLocations={locsLoading}
        />

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? t("creating") : t("submit")}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/procurement/goods-received")}
          >
            {tCommon("cancel")}
          </Button>
        </div>
      </form>
    </div>
  )
}
