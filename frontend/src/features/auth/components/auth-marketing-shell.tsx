"use client";

import { useId, type ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";

import { AuthFeatureRow } from "./auth-feature-row";

export type AuthMarketingFeature = {
  icon: LucideIcon;
  title: string;
  description: string;
};

/**
 * Smooth arc over row index (peaks mid-list); uses logical margin for RTL.
 * Raised midpoint (`bias`) exaggerates the outer bulge so the bow reads at a glance.
 */
function bowMarginInlineStartPx(
  index: number,
  total: number,
  maxOffsetPx: number,
): number {
  if (total <= 0 || maxOffsetPx <= 0) return 0;
  const t = (index + 1) / (total + 1);
  const sine = Math.sin(t * Math.PI);
  /* Blend toward a sharper peak so middle rows step clearly outward */
  const bias = Math.pow(sine, 0.78);
  return Math.round(maxOffsetPx * bias);
}

function AuthMarketingPanelContent({
  features,
  marketingTitle,
  marketingSubtitle,
  headingId,
  variant,
}: {
  features: AuthMarketingFeature[];
  marketingTitle: string;
  marketingSubtitle: string;
  headingId: string;
  variant: "desktop" | "mobile";
}) {
  const t = useTranslations("Auth.marketing");
  const compact = variant === "mobile";
  const featureCount = features.length;
  /* Stronger desktop offset so the content bow is obvious; mobile capped for measure. */
  const bowMaxPx = compact ? 32 : 76;
  const headingInsetPx = 0;

  return (
    <>
      <div style={{ marginInlineStart: headingInsetPx }}>
        <h2
          id={headingId}
          className={cn(
            "text-balance font-semibold tracking-tight text-muted-foreground",
            compact ? "text-sm" : "text-base",
          )}
        >
          {marketingTitle}
        </h2>
        {marketingSubtitle ? (
          <p
            className={cn(
              "text-pretty text-muted-foreground/90",
              compact ? "mt-1 text-[11px] leading-snug" : "mt-1.5 text-xs leading-snug",
            )}
          >
            {marketingSubtitle}
          </p>
        ) : null}
      </div>
      <div className={compact ? "mt-3 space-y-2.5" : "mt-4 flex flex-col gap-3"}>
        {variant === "mobile" ? (
          <>
            {features.slice(0, 3).map((f, i) => (
              <div
                key={`${f.title}-${i}`}
                style={{
                  marginInlineStart: bowMarginInlineStartPx(i, featureCount, bowMaxPx),
                }}
              >
                <AuthFeatureRow {...f} compact supporting />
              </div>
            ))}
            {features.length > 3 ? (
              <details className="group">
                <summary className="cursor-pointer list-none text-pretty text-xs font-medium text-primary underline-offset-4 hover:underline [&::-webkit-details-marker]:hidden">
                  {t("disclosureTrigger")}
                </summary>
                <div className="mt-3 space-y-3 border-t border-border pt-3">
                  {features.slice(3).map((f, i) => {
                    const index = i + 3;
                    return (
                      <div
                        key={`${f.title}-${index}`}
                        style={{
                          marginInlineStart: bowMarginInlineStartPx(
                            index,
                            featureCount,
                            bowMaxPx,
                          ),
                        }}
                      >
                        <AuthFeatureRow {...f} compact supporting />
                      </div>
                    );
                  })}
                </div>
              </details>
            ) : null}
          </>
        ) : (
          features.map((f, i) => (
            <div
              key={`${f.title}-${i}`}
              style={{
                marginInlineStart: bowMarginInlineStartPx(i, featureCount, bowMaxPx),
              }}
            >
              <AuthFeatureRow {...f} supporting />
            </div>
          ))
        )}
      </div>
    </>
  );
}

export type AuthMarketingShellProps = {
  formMaxWidth?: "md" | "lg";
  /** Vertical alignment of columns on `md+` (login often looks better centered). */
  columnAlign?: "center" | "start";
  title: string;
  subtitle: string;
  formIcon: LucideIcon;
  marketingTitle: string;
  marketingSubtitle: string;
  features: AuthMarketingFeature[];
  children: ReactNode;
};

export function AuthMarketingShell({
  formMaxWidth = "md",
  columnAlign = "start",
  title,
  subtitle,
  formIcon: FormIcon,
  marketingTitle,
  marketingSubtitle,
  features,
  children,
}: AuthMarketingShellProps) {
  const baseId = useId();
  const marketingHeadingId = `auth-marketing-heading-${baseId}`;
  const marketingHeadingMobileId = `${marketingHeadingId}-mobile`;
  const maxW = formMaxWidth === "lg" ? "max-w-lg" : "max-w-md";

  return (
    <div className="w-full px-4 py-8">
      <div
        className={cn(
          "mx-auto grid w-full max-w-6xl grid-cols-1 gap-8 md:grid-cols-2 md:gap-12",
          columnAlign === "center" ? "md:items-center" : "md:items-start",
        )}
      >
        <div className="mx-auto w-full md:mx-0">
          <div
            className={cn(
              "mx-auto rounded-2xl border bg-background/80 p-6 shadow-sm backdrop-blur-sm md:mx-0",
              maxW,
            )}
          >
            <div className="text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <FormIcon className="h-6 w-6 text-primary" />
              </div>
              <h1 className="text-balance text-xl font-semibold tracking-tight">
                {title}
              </h1>
              <p className="mt-1.5 text-pretty text-sm text-muted-foreground">
                {subtitle}
              </p>
            </div>
            <div className="mt-6">{children}</div>
          </div>
        </div>

        <aside className="hidden md:block" aria-labelledby={marketingHeadingId}>
          <div className="py-1 ps-0 pe-0 md:py-2">
            <AuthMarketingPanelContent
              features={features}
              marketingTitle={marketingTitle}
              marketingSubtitle={marketingSubtitle}
              headingId={marketingHeadingId}
              variant="desktop"
            />
          </div>
        </aside>

        <section className="md:hidden" aria-labelledby={marketingHeadingMobileId}>
          <div className="pt-2">
            <AuthMarketingPanelContent
              features={features}
              marketingTitle={marketingTitle}
              marketingSubtitle={marketingSubtitle}
              headingId={marketingHeadingMobileId}
              variant="mobile"
            />
          </div>
        </section>
      </div>
    </div>
  );
}
