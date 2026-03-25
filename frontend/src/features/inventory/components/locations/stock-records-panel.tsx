"use client"

import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import type { StockRecordAtLocation } from "../../types/location.types"

export function StockLinesTable({
  records,
}: {
  records: StockRecordAtLocation[]
}) {
  const t = useTranslations("Inventory")

  return (
    <table className="w-full text-sm">
      <caption className="sr-only">{t("locations.subTableCaption")}</caption>
      <thead>
        <tr className="border-b bg-muted/50 text-left">
          <th className="px-4 py-2 font-medium">
            {t("locations.subTableProduct")}
          </th>
          <th className="px-4 py-2 text-right font-medium">
            {t("locations.subTableQty")}
          </th>
          <th className="px-4 py-2 text-right font-medium">
            {t("locations.subTableReserved")}
          </th>
          <th className="px-4 py-2 text-right font-medium">
            {t("locations.subTableAvailable")}
          </th>
        </tr>
      </thead>
      <tbody>
        {records.map((r) => (
          <tr key={r.id} className="border-b last:border-0">
            <td className="px-4 py-2">
              <div className="font-medium">{r.product_name}</div>
              <div className="text-xs text-muted-foreground">
                {r.product_sku}
              </div>
            </td>
            <td className="px-4 py-2 text-right tabular-nums">{r.quantity}</td>
            <td className="px-4 py-2 text-right tabular-nums">
              {r.reserved_quantity}
            </td>
            <td className="px-4 py-2 text-right tabular-nums">
              <span
                className={cn(
                  r.is_low_stock && "font-medium text-destructive",
                )}
              >
                {r.available_quantity}
              </span>
              {r.is_low_stock && (
                <Badge variant="destructive" className="ml-2 text-[10px]">
                  {t("shared.low")}
                </Badge>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
