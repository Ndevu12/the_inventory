"use client"

import { DownloadIcon, FileSpreadsheetIcon, FileTextIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import type { ExportFormat } from "@/types/api-common"

interface ExportButtonsProps {
  onExport: (format: ExportFormat) => void
  exporting: ExportFormat | null
}

export function ExportButtons({ onExport, exporting }: ExportButtonsProps) {
  const t = useTranslations("Reports.shared")
  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        disabled={exporting !== null}
        onClick={() => onExport("csv")}
      >
        {exporting === "csv" ? (
          <DownloadIcon className="size-4 animate-bounce" />
        ) : (
          <FileSpreadsheetIcon className="size-4" />
        )}
        {t("csv")}
      </Button>
      <Button
        variant="outline"
        size="sm"
        disabled={exporting !== null}
        onClick={() => onExport("pdf")}
      >
        {exporting === "pdf" ? (
          <DownloadIcon className="size-4 animate-bounce" />
        ) : (
          <FileTextIcon className="size-4" />
        )}
        {t("pdf")}
      </Button>
    </div>
  )
}
