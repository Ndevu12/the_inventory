"""Report API views — JSON endpoints with optional CSV/PDF export.

Each view delegates to the existing report service layer and returns
structured JSON.  Append ``?export=csv`` or ``?export=pdf`` to any
endpoint to download a file instead.
"""

from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.exports import export_csv
from reports.pdf import export_pdf
from reports.services.inventory_reports import InventoryReportService
from reports.services.order_reports import OrderReportService


class _ExportableAPIView(APIView):
    """Base for report views that support CSV/PDF file downloads."""

    permission_classes = (IsAuthenticated,)

    def _wants_export(self, request):
        return request.query_params.get("export")

    def _export_csv(self, filename, headers, rows):
        return export_csv(filename=filename, headers=headers, rows=rows)

    def _export_pdf(self, filename, title, headers, rows, subtitle=""):
        return export_pdf(
            filename=filename, title=title,
            headers=headers, rows=rows, subtitle=subtitle,
        )

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None


class StockValuationView(_ExportableAPIView):
    """Stock valuation report.

    Query params: ``?method=weighted_average|latest_cost``
    """

    def get(self, request):
        method = request.query_params.get("method", "weighted_average")
        service = InventoryReportService()
        valuations = service.get_stock_valuation(method=method)
        summary = service.get_valuation_summary(method=method)

        items = [
            {
                "sku": v.product.sku,
                "product_name": v.product.name,
                "category": str(v.product.category) if v.product.category else None,
                "total_quantity": v.total_quantity,
                "unit_cost": v.unit_cost,
                "total_value": v.total_value,
                "method": v.method,
            }
            for v in valuations
        ]

        fmt = self._wants_export(request)
        if fmt:
            headers = ["SKU", "Product", "Category", "Qty", "Unit Cost", "Total Value"]
            rows = [[i["sku"], i["product_name"], i["category"] or "", i["total_quantity"], i["unit_cost"], i["total_value"]] for i in items]
            if fmt == "csv":
                return self._export_csv("stock_valuation.csv", headers, rows)
            return self._export_pdf("stock_valuation.pdf", "Stock Valuation Report", headers, rows, f"Method: {method}")

        return Response({
            "method": method,
            "total_products": summary["total_products"],
            "total_quantity": summary["total_quantity"],
            "total_value": str(summary["total_value"]),
            "items": items,
        })


class MovementHistoryView(_ExportableAPIView):
    """Filterable stock movement history.

    Query params: ``?date_from``, ``?date_to``, ``?type``, ``?product``, ``?location``
    """

    def get(self, request):
        service = InventoryReportService()
        movements = service.get_movement_history(
            date_from=self._parse_date(request.query_params.get("date_from")),
            date_to=self._parse_date(request.query_params.get("date_to")),
            movement_type=request.query_params.get("type"),
        )

        items = [
            {
                "id": m.pk,
                "product_sku": m.product.sku,
                "product_name": m.product.name,
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "unit_cost": str(m.unit_cost) if m.unit_cost else None,
                "from_location": str(m.from_location) if m.from_location else None,
                "to_location": str(m.to_location) if m.to_location else None,
                "reference": m.reference,
                "created_at": m.created_at.isoformat(),
                "created_by": str(m.created_by) if m.created_by else None,
            }
            for m in movements[:500]
        ]

        fmt = self._wants_export(request)
        if fmt:
            headers = ["ID", "SKU", "Type", "Qty", "Unit Cost", "From", "To", "Reference", "Date"]
            rows = [[i["id"], i["product_sku"], i["movement_type"], i["quantity"], i["unit_cost"] or "", i["from_location"] or "", i["to_location"] or "", i["reference"], i["created_at"]] for i in items]
            if fmt == "csv":
                return self._export_csv("movement_history.csv", headers, rows)
            return self._export_pdf("movement_history.pdf", "Movement History", headers, rows)

        return Response({"count": len(items), "results": items})


class LowStockReportView(_ExportableAPIView):
    """Products at or below reorder point."""

    def get(self, request):
        service = InventoryReportService()
        products = service.get_low_stock_products()

        items = []
        for p in products:
            total = sum(sr.quantity for sr in p.stock_records.all())
            items.append({
                "sku": p.sku,
                "product_name": p.name,
                "category": str(p.category) if p.category else None,
                "reorder_point": p.reorder_point,
                "total_stock": total,
                "deficit": p.reorder_point - total,
            })

        fmt = self._wants_export(request)
        if fmt:
            headers = ["SKU", "Product", "Category", "Reorder Point", "Stock", "Deficit"]
            rows = [[i["sku"], i["product_name"], i["category"] or "", i["reorder_point"], i["total_stock"], i["deficit"]] for i in items]
            if fmt == "csv":
                return self._export_csv("low_stock.csv", headers, rows)
            return self._export_pdf("low_stock.pdf", "Low Stock Report", headers, rows)

        return Response({"count": len(items), "results": items})


class OverstockReportView(_ExportableAPIView):
    """Products exceeding reorder_point * threshold.

    Query params: ``?threshold`` (default 3)
    """

    def get(self, request):
        threshold = int(request.query_params.get("threshold", 3))
        service = InventoryReportService()
        products = service.get_overstock_products(threshold_multiplier=threshold)

        items = []
        for p in products:
            items.append({
                "sku": p.sku,
                "product_name": p.name,
                "category": str(p.category) if p.category else None,
                "reorder_point": p.reorder_point,
                "total_stock": p.total_stock,
                "threshold": p.reorder_point * threshold,
                "excess": p.total_stock - (p.reorder_point * threshold),
            })

        fmt = self._wants_export(request)
        if fmt:
            headers = ["SKU", "Product", "Category", "Reorder Point", "Stock", "Threshold", "Excess"]
            rows = [[i["sku"], i["product_name"], i["category"] or "", i["reorder_point"], i["total_stock"], i["threshold"], i["excess"]] for i in items]
            if fmt == "csv":
                return self._export_csv("overstock.csv", headers, rows)
            return self._export_pdf("overstock.pdf", "Overstock Report", headers, rows, f"Threshold: {threshold}x reorder point")

        return Response({"count": len(items), "threshold": threshold, "results": items})


class ReservationSummaryView(_ExportableAPIView):
    """Reservation counts and quantities by status.

    Returns aggregate breakdown plus active totals.
    """

    def get(self, request):
        service = InventoryReportService()
        summary = service.get_reservation_summary()

        fmt = self._wants_export(request)
        if fmt:
            headers = ["Status", "Count", "Total Quantity"]
            rows = [
                [info["label"], info["count"], info["total_quantity"]]
                for info in summary["by_status"].values()
            ]
            if fmt == "csv":
                return self._export_csv("reservation_summary.csv", headers, rows)
            return self._export_pdf(
                "reservation_summary.pdf", "Reservation Summary",
                headers, rows,
            )

        return Response(summary)


class AvailabilityReportView(_ExportableAPIView):
    """Per-product availability: total quantity, reserved, and available.

    Query params: ``?category``, ``?product``, ``?export=csv|pdf``
    """

    def get(self, request):
        category_id = request.query_params.get("category")
        product_id = request.query_params.get("product")

        service = InventoryReportService()
        items = service.get_availability_report(
            category_id=int(category_id) if category_id else None,
            product_id=int(product_id) if product_id else None,
        )

        total_reserved_value = sum(
            (item["reserved_value"] for item in items), 0,
        )
        for item in items:
            item["unit_cost"] = str(item["unit_cost"])
            item["reserved_value"] = str(item["reserved_value"])

        fmt = self._wants_export(request)
        if fmt:
            headers = [
                "SKU", "Product", "Category",
                "Total Qty", "Reserved", "Available",
                "Unit Cost", "Reserved Value",
            ]
            rows = [
                [
                    i["sku"], i["product_name"], i["category"] or "",
                    i["total_quantity"], i["reserved_quantity"],
                    i["available_quantity"], i["unit_cost"],
                    i["reserved_value"],
                ]
                for i in items
            ]
            if fmt == "csv":
                return self._export_csv("availability.csv", headers, rows)
            return self._export_pdf(
                "availability.pdf", "Availability Report", headers, rows,
            )

        return Response({
            "count": len(items),
            "total_reserved_value": str(total_reserved_value),
            "results": items,
        })


class PurchaseSummaryView(_ExportableAPIView):
    """Purchase order summary grouped by period.

    Query params: ``?period=daily|weekly|monthly``, ``?date_from``, ``?date_to``
    """

    def get(self, request):
        period = request.query_params.get("period", "monthly")
        date_from = self._parse_date(request.query_params.get("date_from"))
        date_to = self._parse_date(request.query_params.get("date_to"))

        service = OrderReportService()
        data = service.get_purchase_summary(period=period, date_from=date_from, date_to=date_to)
        totals = service.get_purchase_totals(date_from=date_from, date_to=date_to)

        items = [
            {"period": str(row["period"]), "order_count": row["order_count"], "total": str(row["total_cost"])}
            for row in data
        ]

        fmt = self._wants_export(request)
        if fmt:
            headers = ["Period", "Orders", "Total Cost"]
            rows = [[i["period"], i["order_count"], i["total"]] for i in items]
            if fmt == "csv":
                return self._export_csv("purchase_summary.csv", headers, rows)
            return self._export_pdf("purchase_summary.pdf", "Purchase Summary", headers, rows, f"Period: {period}")

        return Response({"period": period, "totals": totals, "results": items})


class SalesSummaryView(_ExportableAPIView):
    """Sales order summary grouped by period.

    Query params: ``?period=daily|weekly|monthly``, ``?date_from``, ``?date_to``
    """

    def get(self, request):
        period = request.query_params.get("period", "monthly")
        date_from = self._parse_date(request.query_params.get("date_from"))
        date_to = self._parse_date(request.query_params.get("date_to"))

        service = OrderReportService()
        data = service.get_sales_summary(period=period, date_from=date_from, date_to=date_to)
        totals = service.get_sales_totals(date_from=date_from, date_to=date_to)

        items = [
            {"period": str(row["period"]), "order_count": row["order_count"], "total": str(row["total_revenue"])}
            for row in data
        ]

        fmt = self._wants_export(request)
        if fmt:
            headers = ["Period", "Orders", "Total Revenue"]
            rows = [[i["period"], i["order_count"], i["total"]] for i in items]
            if fmt == "csv":
                return self._export_csv("sales_summary.csv", headers, rows)
            return self._export_pdf("sales_summary.pdf", "Sales Summary", headers, rows, f"Period: {period}")

        return Response({"period": period, "totals": totals, "results": items})


class ProductExpiryView(_ExportableAPIView):
    """Product expiry report — expiring and expired lots.

    Query params:
        ``?days_ahead=30`` — look-ahead window (default 30)
        ``?product=<id>`` — filter by product
        ``?location=<id>`` — filter by stock location
    """

    def _get_filters(self, request):
        days_ahead = int(request.query_params.get("days_ahead", 30))
        days_ahead = max(1, days_ahead)

        product = self._resolve_fk(request, "product", "inventory.Product")
        location = self._resolve_fk(request, "location", "inventory.StockLocation")
        return days_ahead, product, location

    @staticmethod
    def _resolve_fk(request, param, model_label):
        pk = request.query_params.get(param)
        if not pk:
            return None
        from django.apps import apps
        model = apps.get_model(model_label)
        try:
            return model.objects.get(pk=pk)
        except (model.DoesNotExist, ValueError):
            return None

    def get(self, request):
        service = InventoryReportService()
        days_ahead, product, location = self._get_filters(request)

        expiring = service.get_expiring_lots(
            days_ahead=days_ahead, product=product, location=location,
        )
        expired = service.get_expired_lots(
            product=product, location=location,
        )

        def _lot_dict(lot, status):
            return {
                "status": status,
                "product_id": lot.product_id,
                "sku": lot.product.sku,
                "product_name": lot.product.name,
                "lot_number": lot.lot_number,
                "expiry_date": lot.expiry_date.isoformat(),
                "days_to_expiry": lot.days_to_expiry(),
                "quantity_remaining": lot.quantity_remaining,
                "quantity_received": lot.quantity_received,
                "supplier": str(lot.supplier) if lot.supplier else None,
            }

        items = [_lot_dict(lot, "expired") for lot in expired]
        items += [_lot_dict(lot, "expiring") for lot in expiring]

        fmt = self._wants_export(request)
        if fmt:
            headers = [
                "Status", "SKU", "Product", "Lot Number", "Expiry Date",
                "Days Left", "Qty Remaining", "Qty Received", "Supplier",
            ]
            rows = [
                [
                    i["status"], i["sku"], i["product_name"], i["lot_number"],
                    i["expiry_date"], i["days_to_expiry"],
                    i["quantity_remaining"], i["quantity_received"],
                    i["supplier"] or "",
                ]
                for i in items
            ]
            if fmt == "csv":
                return self._export_csv(f"expiry_report_{days_ahead}d.csv", headers, rows)
            return self._export_pdf(
                f"expiry_report_{days_ahead}d.pdf",
                "Product Expiry Report",
                headers,
                rows,
                f"Look-ahead: {days_ahead} days",
            )

        return Response({
            "days_ahead": days_ahead,
            "expired_count": len([i for i in items if i["status"] == "expired"]),
            "expiring_count": len([i for i in items if i["status"] == "expiring"]),
            "results": items,
        })


class LotHistoryView(_ExportableAPIView):
    """Full movement chain for a specific lot.

    Query params:
        ``?product=<id>`` — product ID (required)
        ``?lot_number=<str>`` — lot number (required)
    """

    def get(self, request):
        product_id = request.query_params.get("product")
        lot_number = request.query_params.get("lot_number")

        if not product_id or not lot_number:
            return Response(
                {"detail": "Both 'product' and 'lot_number' query params are required."},
                status=400,
            )

        product = self._resolve_fk(request, "product", "inventory.Product")
        if product is None:
            return Response({"detail": "Product not found."}, status=404)

        service = InventoryReportService()
        movements = service.get_lot_history(product=product, lot_number=lot_number)

        items = [
            {
                "id": m.pk,
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "unit_cost": str(m.unit_cost) if m.unit_cost else None,
                "from_location": str(m.from_location) if m.from_location else None,
                "to_location": str(m.to_location) if m.to_location else None,
                "reference": m.reference,
                "created_at": m.created_at.isoformat(),
                "created_by": str(m.created_by) if m.created_by else None,
                "lot_allocations": [
                    {
                        "lot_number": alloc.stock_lot.lot_number,
                        "quantity": alloc.quantity,
                    }
                    for alloc in m.lot_allocations.all()
                ],
            }
            for m in movements
        ]

        fmt = self._wants_export(request)
        if fmt:
            headers = [
                "ID", "Type", "Qty", "Unit Cost", "From", "To",
                "Reference", "Date", "Created By",
            ]
            rows = [
                [
                    i["id"], i["movement_type"], i["quantity"],
                    i["unit_cost"] or "", i["from_location"] or "",
                    i["to_location"] or "", i["reference"],
                    i["created_at"], i["created_by"] or "",
                ]
                for i in items
            ]
            if fmt == "csv":
                return self._export_csv(f"lot_history_{lot_number}.csv", headers, rows)
            return self._export_pdf(
                f"lot_history_{lot_number}.pdf",
                f"Lot History — {lot_number}",
                headers,
                rows,
            )

        return Response({
            "product_id": product.pk,
            "lot_number": lot_number,
            "movement_count": len(items),
            "results": items,
        })

    @staticmethod
    def _resolve_fk(request, param, model_label):
        pk = request.query_params.get(param)
        if not pk:
            return None
        from django.apps import apps
        model = apps.get_model(model_label)
        try:
            return model.objects.get(pk=pk)
        except (model.DoesNotExist, ValueError):
            return None


class VarianceReportView(_ExportableAPIView):
    """Inventory variance report with filtering by cycle, product, and variance type.

    Query params: ``?cycle_id``, ``?product_id``, ``?variance_type=shortage|surplus|match``
    """

    def get(self, request):
        cycle_id = request.query_params.get("cycle_id")
        product_id = request.query_params.get("product_id")
        variance_type = request.query_params.get("variance_type")

        cycle_id = int(cycle_id) if cycle_id else None
        product_id = int(product_id) if product_id else None

        service = InventoryReportService()
        variances = service.get_variance_report(
            cycle_id=cycle_id,
            product_id=product_id,
            variance_type=variance_type,
        )
        summary = service.get_variance_summary(cycle_id=cycle_id)

        items = [
            {
                "id": v.pk,
                "cycle_id": v.cycle_id,
                "cycle_name": v.cycle.name,
                "product_sku": v.product.sku,
                "product_name": v.product.name,
                "location": str(v.location),
                "variance_type": v.variance_type,
                "variance_type_display": v.get_variance_type_display(),
                "system_quantity": v.system_quantity,
                "physical_quantity": v.physical_quantity,
                "variance_quantity": v.variance_quantity,
                "resolution": v.resolution,
                "root_cause": v.root_cause,
                "resolved_by": str(v.resolved_by) if v.resolved_by else None,
                "resolved_at": v.resolved_at.isoformat() if v.resolved_at else None,
                "created_at": v.created_at.isoformat(),
            }
            for v in variances[:500]
        ]

        fmt = self._wants_export(request)
        if fmt:
            headers = [
                "ID", "Cycle", "SKU", "Product", "Location", "Type",
                "System Qty", "Physical Qty", "Variance", "Resolution",
                "Root Cause", "Resolved By", "Date",
            ]
            rows = [
                [
                    i["id"], i["cycle_name"], i["product_sku"],
                    i["product_name"], i["location"],
                    i["variance_type_display"], i["system_quantity"],
                    i["physical_quantity"], i["variance_quantity"],
                    i["resolution"] or "", i["root_cause"],
                    i["resolved_by"] or "", i["created_at"],
                ]
                for i in items
            ]
            subtitle_parts = []
            if cycle_id:
                subtitle_parts.append(f"Cycle ID: {cycle_id}")
            if variance_type:
                subtitle_parts.append(f"Type: {variance_type}")
            subtitle = " | ".join(subtitle_parts) if subtitle_parts else ""

            if fmt == "csv":
                return self._export_csv("variance_report.csv", headers, rows)
            return self._export_pdf(
                "variance_report.pdf", "Inventory Variance Report",
                headers, rows, subtitle,
            )

        return Response({
            "count": len(items),
            "summary": summary,
            "results": items,
        })


class CycleHistoryView(_ExportableAPIView):
    """Summary of past inventory cycles and their reconciliation status."""

    def get(self, request):
        service = InventoryReportService()
        cycles = service.get_cycle_history()

        fmt = self._wants_export(request)
        if fmt:
            headers = [
                "ID", "Name", "Status", "Location", "Scheduled Date",
                "Started At", "Completed At", "Lines", "Variances",
                "Shortages", "Surpluses", "Matches", "Net Variance",
            ]
            rows = [
                [
                    c["id"], c["name"], c["status_display"],
                    c["location"] or "", str(c["scheduled_date"]),
                    str(c["started_at"] or ""), str(c["completed_at"] or ""),
                    c["total_lines"], c["total_variances"],
                    c["shortages"], c["surpluses"], c["matches"],
                    c["net_variance"],
                ]
                for c in cycles
            ]
            if fmt == "csv":
                return self._export_csv("cycle_history.csv", headers, rows)
            return self._export_pdf(
                "cycle_history.pdf", "Cycle Count History",
                headers, rows,
            )

        return Response({"count": len(cycles), "results": cycles})


class ProductTraceabilityView(_ExportableAPIView):
    """Full movement chain for a product + lot (GS1 traceability).

    Query params: ``?product={sku}&lot={lot_number}``
    """

    def get(self, request):
        sku = request.query_params.get("product")
        lot_number = request.query_params.get("lot")

        if not sku or not lot_number:
            return Response(
                {"detail": "Both 'product' (SKU) and 'lot' (lot number) query parameters are required."},
                status=400,
            )

        service = InventoryReportService()
        result = service.get_product_traceability(sku=sku, lot_number=lot_number)

        if result is None:
            return Response(
                {"detail": "Product or lot not found."},
                status=404,
            )

        fmt = self._wants_export(request)
        if fmt:
            headers = ["Action", "Date", "Quantity", "Location / From", "To", "Sales Order"]
            rows = []
            for entry in result["chain"]:
                rows.append([
                    entry.get("action", ""),
                    entry.get("date", ""),
                    entry.get("quantity", ""),
                    entry.get("location") or entry.get("from") or "",
                    entry.get("to", ""),
                    entry.get("sales_order", ""),
                ])
            subtitle = f"Product: {sku} | Lot: {lot_number}"
            if fmt == "csv":
                return self._export_csv("product_traceability.csv", headers, rows)
            return self._export_pdf(
                "product_traceability.pdf",
                "Product Traceability Report",
                headers, rows, subtitle,
            )

        return Response(result)
