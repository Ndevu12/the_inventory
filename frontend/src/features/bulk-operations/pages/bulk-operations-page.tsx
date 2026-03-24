"use client";

import { useTranslations } from "next-intl";
import { PageHeader } from "@/components/layout/page-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowRightLeftIcon, ScaleIcon, DollarSignIcon } from "lucide-react";
import { BulkTransferForm } from "../components/bulk-transfer-form";
import { BulkAdjustmentForm } from "../components/bulk-adjustment-form";
import { BulkRevalueForm } from "../components/bulk-revalue-form";

export function BulkOperationsPage() {
  const t = useTranslations("BulkOperations");

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title={t("page.title")}
        description={t("page.description")}
      />

      <Tabs defaultValue="transfer" className="space-y-6">
        <TabsList>
          <TabsTrigger value="transfer" className="gap-1.5">
            <ArrowRightLeftIcon className="size-4" />
            {t("tabs.transfer")}
          </TabsTrigger>
          <TabsTrigger value="adjustment" className="gap-1.5">
            <ScaleIcon className="size-4" />
            {t("tabs.adjustment")}
          </TabsTrigger>
          <TabsTrigger value="revalue" className="gap-1.5">
            <DollarSignIcon className="size-4" />
            {t("tabs.revalue")}
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
