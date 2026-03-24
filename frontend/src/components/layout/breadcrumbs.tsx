"use client";

import { Link, usePathname } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { Fragment } from "react";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

/** Matches ``Breadcrumbs`` keys in locale JSON (except ``home``, used for root). */
const BREADCRUMB_SEGMENT_KEYS = new Set([
  "products",
  "categories",
  "stock",
  "locations",
  "records",
  "movements",
  "lots",
  "reservations",
  "cycle-counts",
  "bulk-operations",
  "procurement",
  "suppliers",
  "purchase-orders",
  "goods-received",
  "sales",
  "customers",
  "sales-orders",
  "dispatches",
  "reports",
  "stock-valuation",
  "movement-history",
  "low-stock",
  "overstock",
  "purchase-summary",
  "sales-summary",
  "availability",
  "product-expiry",
  "variances",
  "traceability",
  "audit-log",
  "settings",
  "members",
  "new",
  "edit",
]);

function formatUnknownSegment(segment: string): string {
  return segment
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function Breadcrumbs() {
  const pathname = usePathname();
  const t = useTranslations("Breadcrumbs");
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) return null;

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink render={<Link href="/" />}>{t("home")}</BreadcrumbLink>
        </BreadcrumbItem>
        {segments.map((segment, index) => {
          const href = "/" + segments.slice(0, index + 1).join("/");
          const isLast = index === segments.length - 1;
          const label = BREADCRUMB_SEGMENT_KEYS.has(segment)
            ? t(segment)
            : formatUnknownSegment(segment);

          return (
            <Fragment key={href}>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                {isLast ? (
                  <BreadcrumbPage>{label}</BreadcrumbPage>
                ) : (
                  <BreadcrumbLink render={<Link href={href} />}>
                    {label}
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </Fragment>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
