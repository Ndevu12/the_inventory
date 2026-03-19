"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Fragment } from "react";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

const LABEL_MAP: Record<string, string> = {
  products: "Products",
  categories: "Categories",
  stock: "Stock",
  locations: "Locations",
  records: "Records",
  movements: "Movements",
  lots: "Lots",
  reservations: "Reservations",
  "cycle-counts": "Cycle Counts",
  "bulk-operations": "Bulk Operations",
  procurement: "Procurement",
  suppliers: "Suppliers",
  "purchase-orders": "Purchase Orders",
  "goods-received": "Goods Received",
  sales: "Sales",
  customers: "Customers",
  "sales-orders": "Sales Orders",
  dispatches: "Dispatches",
  reports: "Reports",
  "stock-valuation": "Stock Valuation",
  "movement-history": "Movement History",
  "low-stock": "Low Stock",
  overstock: "Overstock",
  "purchase-summary": "Purchase Summary",
  "sales-summary": "Sales Summary",
  availability: "Availability",
  "product-expiry": "Product Expiry",
  variances: "Variances",
  traceability: "Traceability",
  "audit-log": "Audit Log",
  settings: "Settings",
  members: "Team Members",
  new: "New",
  edit: "Edit",
};

function formatSegment(segment: string): string {
  return (
    LABEL_MAP[segment] ??
    segment
      .replace(/-/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) return null;

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink render={<Link href="/" />}>Dashboard</BreadcrumbLink>
        </BreadcrumbItem>
        {segments.map((segment, index) => {
          const href = "/" + segments.slice(0, index + 1).join("/");
          const isLast = index === segments.length - 1;
          const label = formatSegment(segment);

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
