"use client";

import { PageHeader } from "@/components/layout/page-header";
import { MovementForm } from "../components/movements/movement-form";

export function MovementCreatePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Record Movement"
        description="Create a new stock movement (receive, issue, transfer, or adjustment)."
      />
      <MovementForm />
    </div>
  );
}
