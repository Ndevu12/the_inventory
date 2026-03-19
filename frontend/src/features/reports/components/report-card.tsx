"use client"

import Link from "next/link"
import {
  DollarSign,
  ArrowLeftRight,
  AlertTriangle,
  TrendingUp,
  ShoppingCart,
  Receipt,
  PackageCheck,
  Clock,
  Scale,
  Search,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import type { ReportDefinition } from "../helpers/report-constants"

const ICON_MAP: Record<string, LucideIcon> = {
  DollarSign,
  ArrowLeftRight,
  AlertTriangle,
  TrendingUp,
  ShoppingCart,
  Receipt,
  PackageCheck,
  Clock,
  Scale,
  Search,
}

interface ReportCardProps {
  report: ReportDefinition
}

export function ReportCard({ report }: ReportCardProps) {
  const Icon = ICON_MAP[report.icon] ?? DollarSign

  return (
    <Link href={report.path} className="group">
      <Card className="h-full transition-colors group-hover:border-primary/50 group-hover:bg-muted/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Icon className="size-5" />
            </div>
            <div className="space-y-1">
              <CardTitle>{report.name}</CardTitle>
              <CardDescription>{report.description}</CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>
    </Link>
  )
}
