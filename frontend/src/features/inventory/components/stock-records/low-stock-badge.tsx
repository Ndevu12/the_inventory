"use client";

import { AlertTriangleIcon, CheckCircleIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface LowStockBadgeProps {
  isLowStock: boolean;
}

export function LowStockBadge({ isLowStock }: LowStockBadgeProps) {
  if (isLowStock) {
    return (
      <Badge variant="destructive">
        <AlertTriangleIcon data-icon="inline-start" />
        Low Stock
      </Badge>
    );
  }

  return (
    <Badge variant="secondary">
      <CheckCircleIcon data-icon="inline-start" />
      OK
    </Badge>
  );
}
