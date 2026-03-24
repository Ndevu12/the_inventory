"use client"

import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { PlusIcon } from "lucide-react"
import { Link } from "@/i18n/navigation"
import { MovementTable } from "../components/movements/movement-table"

export function MovementListPage() {
  const t = useTranslations("Inventory")

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("movements.listTitle")}
        description={t("movements.listDescription")}
        actions={
          <Button asChild size="sm">
            <Link href="/stock/movements/new">
              <PlusIcon className="mr-1.5 size-4" />
              {t("movements.newMovement")}
            </Link>
          </Button>
        }
      />
      <MovementTable />
    </div>
  )
}
