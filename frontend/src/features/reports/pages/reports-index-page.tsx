"use client"

import { PageHeader } from "@/components/layout/page-header"
import { ReportCard } from "../components/report-card"
import { REPORT_DEFINITIONS } from "../helpers/report-constants"

export function ReportsIndexPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Reports"
        description="Generate and export inventory, procurement, and sales reports"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {REPORT_DEFINITIONS.map((report) => (
          <ReportCard key={report.id} report={report} />
        ))}
      </div>
    </div>
  )
}
