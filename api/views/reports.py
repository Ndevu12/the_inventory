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
