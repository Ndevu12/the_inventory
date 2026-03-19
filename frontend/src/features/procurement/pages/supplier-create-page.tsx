"use client"

import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { PageHeader } from "@/components/layout/page-header"
import { useCreateSupplier } from "../hooks/use-suppliers"
import {
  createSupplierSchema,
  type CreateSupplierFormValues,
} from "../helpers/supplier-schemas"
import { SupplierForm } from "../components/suppliers/supplier-form"

export function SupplierCreatePage() {
  const router = useRouter()
  const createMutation = useCreateSupplier()

  const form = useForm<CreateSupplierFormValues>({
    resolver: zodResolver(createSupplierSchema),
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
        toast.success(`Supplier "${supplier.name}" created`)
        router.push("/suppliers")
      },
      onError: () => {
        toast.error("Failed to create supplier")
      },
    })
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="New Supplier"
        description="Add a new supplier to your directory"
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
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Supplier"}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}
