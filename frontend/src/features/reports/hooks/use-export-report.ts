import * as React from "react"
import { toast } from "sonner"
import { triggerDownload } from "../helpers/export-helpers"
import type { ExportFormat } from "@/types/api-common"

export function useExportReport(
  reportPath: string,
  params?: Record<string, string>,
) {
  const [exporting, setExporting] = React.useState<ExportFormat | null>(null)

  const handleExport = React.useCallback(
    async (format: ExportFormat) => {
      setExporting(format)
      try {
        await triggerDownload(reportPath, format, params)
        toast.success(`${format.toUpperCase()} exported successfully`)
      } catch {
        toast.error(`Failed to export ${format.toUpperCase()}`)
      } finally {
        setExporting(null)
      }
    },
    [reportPath, params],
  )

  return { exporting, handleExport }
}
