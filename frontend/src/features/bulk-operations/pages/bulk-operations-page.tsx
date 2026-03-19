"use client";

import { PageHeader } from "@/components/layout/page-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowRightLeftIcon, ScaleIcon, DollarSignIcon } from "lucide-react";
import { BulkTransferForm } from "../components/bulk-transfer-form";
import { BulkAdjustmentForm } from "../components/bulk-adjustment-form";
import { BulkRevalueForm } from "../components/bulk-revalue-form";

export function BulkOperationsPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Bulk Operations"
        description="Perform stock transfers, adjustments, and revaluations in bulk."
      />

      <Tabs defaultValue="transfer" className="space-y-6">
        <TabsList>
          <TabsTrigger value="transfer" className="gap-1.5">
            <ArrowRightLeftIcon className="size-4" />
            Bulk Transfer
          </TabsTrigger>
          <TabsTrigger value="adjustment" className="gap-1.5">
            <ScaleIcon className="size-4" />
            Bulk Adjustment
          </TabsTrigger>
          <TabsTrigger value="revalue" className="gap-1.5">
            <DollarSignIcon className="size-4" />
            Bulk Revalue
          </TabsTrigger>
        </TabsList>

        <TabsContent value="transfer">
          <BulkTransferForm />
        </TabsContent>
        <TabsContent value="adjustment">
          <BulkAdjustmentForm />
        </TabsContent>
        <TabsContent value="revalue">
          <BulkRevalueForm />
        </TabsContent>
      </Tabs>
    </div>
  );
}
