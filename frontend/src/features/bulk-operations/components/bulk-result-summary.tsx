"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2Icon, XCircleIcon, AlertTriangleIcon } from "lucide-react";
import type { BulkOperationResult } from "../api/bulk-api";

interface BulkResultSummaryProps {
  result: BulkOperationResult;
  onReset: () => void;
}

export function BulkResultSummary({ result, onReset }: BulkResultSummaryProps) {
  const allSucceeded = result.failure_count === 0;
  const allFailed = result.success_count === 0;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            {allSucceeded ? (
              <CheckCircle2Icon className="size-6 text-emerald-500" />
            ) : allFailed ? (
              <XCircleIcon className="size-6 text-destructive" />
            ) : (
              <AlertTriangleIcon className="size-6 text-amber-500" />
            )}
            <div>
              <CardTitle>
                {allSucceeded
                  ? "Operation Completed Successfully"
                  : allFailed
                    ? "Operation Failed"
                    : "Operation Partially Completed"}
              </CardTitle>
              <CardDescription>
                {result.success_count} of {result.total_count} items processed
                successfully
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-lg border p-4 text-center">
              <p className="text-2xl font-bold">{result.total_count}</p>
              <p className="text-sm text-muted-foreground">Total</p>
            </div>
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-center dark:border-emerald-900 dark:bg-emerald-950">
              <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">
                {result.success_count}
              </p>
              <p className="text-sm text-emerald-600 dark:text-emerald-500">
                Succeeded
              </p>
            </div>
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center dark:border-red-900 dark:bg-red-950">
              <p className="text-2xl font-bold text-red-700 dark:text-red-400">
                {result.failure_count}
              </p>
              <p className="text-sm text-red-600 dark:text-red-500">Failed</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {result.errors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">Errors</CardTitle>
            <CardDescription>
              The following items could not be processed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {result.errors.map((err, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 rounded-md border border-destructive/30 bg-destructive/5 p-3"
                >
                  <XCircleIcon className="mt-0.5 size-4 shrink-0 text-destructive" />
                  <div className="text-sm">
                    <span className="font-medium">
                      Item #{err.index + 1} (Product {err.product_id})
                    </span>
                    <span className="text-muted-foreground"> — {err.error}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Button onClick={onReset}>Start New Operation</Button>
    </div>
  );
}
