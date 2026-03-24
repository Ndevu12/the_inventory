"use client";

import { AlertCircle } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/types/api-common";

function isApiError(err: unknown): err is ApiError {
  return (
    typeof err === "object" &&
    err !== null &&
    "message" in err &&
    typeof (err as ApiError).message === "string"
  );
}

export function getDashboardErrorMessage(
  error: unknown,
  fallbackMessage: string,
): string {
  if (isApiError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return fallbackMessage;
}

export function DashboardWidgetError({
  message,
  onRetry,
  minHeight,
  className,
}: {
  message: string;
  onRetry?: () => void;
  minHeight?: string;
  className?: string;
}) {
  const t = useTranslations("Dashboard.error");
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 rounded-md border border-destructive/30 bg-destructive/5 px-4 py-6 text-center ${className ?? ""}`}
      style={minHeight ? { minHeight } : undefined}
    >
      <AlertCircle className="size-5 shrink-0 text-destructive" aria-hidden />
      <p className="max-w-md text-sm text-muted-foreground">{message}</p>
      {onRetry ? (
        <Button type="button" variant="outline" size="sm" onClick={() => onRetry()}>
          {t("retry")}
        </Button>
      ) : null}
    </div>
  );
}
