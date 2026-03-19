"use client"

import * as React from "react"
import { use } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { PageHeader } from "@/components/layout/page-header"
import { useSupplier, useUpdateSupplier } from "../hooks/use-suppliers"
import {
  editSupplierSchema,
  type EditSupplierFormValues,
} from "../helpers/supplier-schemas"
import { SupplierForm } from "../components/suppliers/supplier-form"

interface SupplierEditPageProps {
  params: Promise<{ id: string }>
}

export function SupplierEditPage({ params }: SupplierEditPageProps) {
  const { id } = use(params)
  const supplierId = Number(id)
  const router = useRouter()
  const { data: supplier, isLoading } = useSupplier(supplierId)
  const updateMutation = useUpdateSupplier()

  const form = useForm<EditSupplierFormValues>({
    resolver: zodResolver(editSupplierSchema),
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

  React.useEffect(() => {
    if (supplier) {
      form.reset({
        code: supplier.code,
        name: supplier.name,
        contact_name: supplier.contact_name ?? "",
        email: supplier.email ?? "",
        phone: supplier.phone ?? "",
        address: supplier.address ?? "",
        lead_time_days: supplier.lead_time_days,
        payment_terms: supplier.payment_terms,
        is_active: supplier.is_active,
        notes: supplier.notes ?? "",
      })
    }
  }, [supplier, form])

  function onSubmit(values: EditSupplierFormValues) {
    updateMutation.mutate(
      { id: supplierId, payload: values },
      {
        onSuccess: () => {
          toast.success(`Supplier "${values.name}" updated`)
          router.push("/suppliers")
        },
        onError: () => {
          toast.error("Failed to update supplier")
        },
      }
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

  if (!supplier) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-6">
        <p className="text-muted-foreground">Supplier not found</p>
        <Button variant="outline" render={<Link href="/suppliers" />}>
          Back to Suppliers
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={`Edit ${supplier.name}`}
        description="Update supplier details"
      />

      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Card>
          <CardContent className="pt-6">
            <SupplierForm form={form} />
          </CardContent>
          <CardFooter className="flex justify-end gap-2">
            <Button variant="outline" render={<Link href="/suppliers" />}>
              Cancel
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}
