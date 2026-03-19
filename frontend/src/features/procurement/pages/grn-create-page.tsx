"use client"

import { useRouter } from "next/navigation"
import { useForm, type Resolver } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/layout/page-header"
import { GRNForm } from "../components/grn/grn-form"
import { useCreateGRN, usePurchaseOrders, useGRNLocations } from "../hooks/use-grn"
import {
  createGRNSchema,
  type CreateGRNFormValues,
} from "../helpers/grn-schemas"

export function GRNCreatePage() {
  const router = useRouter()
  const createMutation = useCreateGRN()
  const { data: poData, isLoading: posLoading } = usePurchaseOrders()
  const { data: locData, isLoading: locsLoading } = useGRNLocations()

  const purchaseOrders = poData?.results ?? []
  const locations = locData?.results ?? []

  const form = useForm<CreateGRNFormValues>({
    resolver: zodResolver(createGRNSchema) as Resolver<CreateGRNFormValues>,
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
        toast.success(`GRN "${grn.grn_number}" created`)
        router.push("/procurement/goods-received")
      },
      onError: (error) => {
        const message =
          (error as { message?: string }).message ?? "Failed to create GRN"
        toast.error(message)
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="New Goods Received Note"
        description="Record goods received from a purchase order"
      />

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
            {createMutation.isPending ? "Creating..." : "Create GRN"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/procurement/goods-received")}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
