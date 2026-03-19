"use client";

import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { PlusIcon } from "lucide-react";
import Link from "next/link";
import { MovementTable } from "../components/movements/movement-table";

export function MovementListPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Stock Movements"
        description="View all stock movements across your inventory."
        actions={
          <Button asChild size="sm">
            <Link href="/stock/movements/new">
              <PlusIcon className="mr-1.5 size-4" />
              New Movement
            </Link>
          </Button>
        }
      />
      <MovementTable />
    </div>
  );
}
