"use client"

import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { MovementForm } from "../components/movements/movement-form"

export function MovementCreatePage() {
  const t = useTranslations("Inventory")

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("movements.createTitle")}
        description={t("movements.createDescription")}
      />
      <MovementForm />
    </div>
  )
}
