"use client"

import { useTranslations } from "next-intl"
import { PageHeader } from "@/components/layout/page-header"
import { ReportCard } from "../components/report-card"
import { REPORT_DEFINITIONS } from "../helpers/report-constants"

export function ReportsIndexPage() {
  const t = useTranslations("Reports.index")
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {REPORT_DEFINITIONS.map((report) => (
          <ReportCard key={report.id} report={report} />
        ))}
      </div>
    </div>
  )
}
