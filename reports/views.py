"""Report views for the Wagtail admin.

All views are read-only and follow the project's OOP standard.
Each view supports CSV export via ``?export=csv``.
"""

from django.views.generic import ListView, TemplateView
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin

from inventory.models import StockMovement

from reports.exports import CSVExportMixin
from reports.filters import MovementHistoryFilter
from reports.services.inventory_reports import InventoryReportService
from reports.services.order_reports import OrderReportService


# =====================================================================
# Stock Valuation
# =====================================================================


class StockValuationView(CSVExportMixin, WagtailAdminTemplateMixin, TemplateView):
    """Stock valuation report with weighted-average and latest-cost methods."""

    template_name = "reports/stock_valuation.html"
    page_title = "Stock Valuation"
    header_icon = "doc-full"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = InventoryReportService()

        method = self.request.GET.get("method", "weighted_average")
        if method not in service.VALUATION_METHODS:
            method = "weighted_average"

        valuations = service.get_stock_valuation(method=method)
        summary = service.get_valuation_summary(method=method)

        context["valuations"] = valuations
        context["summary"] = summary
        context["current_method"] = method
        context["methods"] = service.VALUATION_METHODS
        return context

    def _get_export_data(self):
        service = InventoryReportService()
        method = self.request.GET.get("method", "weighted_average")
        if method not in service.VALUATION_METHODS:
            method = "weighted_average"
        valuations = service.get_stock_valuation(method=method)
        headers = ["SKU", "Product", "Category", "Quantity", "Unit Cost", "Total Value", "Method"]
        rows = [
            [
                v.product.sku,
                v.product.name,
                str(v.product.category or ""),
                v.total_quantity,
                v.unit_cost,
                v.total_value,
                v.method,
            ]
            for v in valuations
        ]
        return method, headers, rows

    def get_csv_data(self):
        method, headers, rows = self._get_export_data()
        return f"stock_valuation_{method}.csv", headers, rows

    def get_pdf_data(self):
        method, headers, rows = self._get_export_data()
        return (
            f"stock_valuation_{method}.pdf",
            "Stock Valuation Report",
            headers,
            rows,
            f"Method: {method.replace('_', ' ').title()}",
        )


# =====================================================================
# Movement History
# =====================================================================


class MovementHistoryView(CSVExportMixin, WagtailAdminTemplateMixin, ListView):
    """Filterable, paginated movement history with audit trail."""

    template_name = "reports/movement_history.html"
    context_object_name = "movements"
    paginate_by = 50
    page_title = "Movement History"
    header_icon = "history"

    def get_queryset(self):
        qs = (
            StockMovement.objects
            .select_related(
                "product", "from_location", "to_location", "created_by",
            )
            .order_by("-created_at")
        )
        self.filterset = MovementHistoryFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        context["total_count"] = self.filterset.qs.count()
        return context

    def _get_export_data(self):
        qs = self.get_queryset()
        headers = [
            "Date", "Type", "SKU", "Product", "Quantity",
            "From Location", "To Location", "Unit Cost",
            "Reference", "Notes", "Created By",
        ]
        rows = [
            [
                m.created_at,
                m.get_movement_type_display(),
                m.product.sku,
                m.product.name,
                m.quantity,
                str(m.from_location or ""),
                str(m.to_location or ""),
                m.unit_cost,
                m.reference,
                m.notes,
                str(m.created_by or ""),
            ]
            for m in qs[:5000]
        ]
        return headers, rows

    def get_csv_data(self):
        headers, rows = self._get_export_data()
        return "movement_history.csv", headers, rows

    def get_pdf_data(self):
        headers, rows = self._get_export_data()
        return (
            "movement_history.pdf",
            "Movement History",
            headers,
            rows,
            f"{len(rows)} movements",
        )


# =====================================================================
# Low Stock & Overstock
# =====================================================================


class LowStockReportView(CSVExportMixin, WagtailAdminTemplateMixin, TemplateView):
    """Low-stock report showing products at or below their reorder point."""

    template_name = "reports/low_stock_report.html"
    page_title = "Low Stock Report"
    header_icon = "warning"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = InventoryReportService()
        context["products"] = service.get_low_stock_products()
        context["total_count"] = context["products"].count()
        return context

    def _get_export_data(self):
        service = InventoryReportService()
        products = service.get_low_stock_products()
        headers = ["SKU", "Product", "Category", "Reorder Point", "Locations & Stock"]
        rows = [
            [
                p.sku,
                p.name,
                str(p.category or ""),
                p.reorder_point,
                "; ".join(
                    f"{r.location.name}: {r.quantity}"
                    for r in p.stock_records.all()
                ),
            ]
            for p in products
        ]
        return headers, rows

    def get_csv_data(self):
        headers, rows = self._get_export_data()
        return "low_stock_report.csv", headers, rows

    def get_pdf_data(self):
        headers, rows = self._get_export_data()
        return (
            "low_stock_report.pdf",
            "Low Stock Report",
            headers,
            rows,
            f"{len(rows)} product(s) at or below reorder point",
        )


class OverstockReportView(CSVExportMixin, WagtailAdminTemplateMixin, TemplateView):
    """Overstock report showing products with excessive inventory."""

    template_name = "reports/overstock_report.html"
    page_title = "Overstock Report"
    header_icon = "plus-inverse"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = InventoryReportService()

        multiplier = self.request.GET.get("threshold", 3)
        try:
            multiplier = int(multiplier)
        except (ValueError, TypeError):
            multiplier = 3

        products = service.get_overstock_products(
            threshold_multiplier=multiplier,
        )
        context["products"] = products
        context["total_count"] = products.count()
        context["threshold_multiplier"] = multiplier
        return context

    def _get_export_data(self):
        service = InventoryReportService()
        multiplier = self.request.GET.get("threshold", 3)
        try:
            multiplier = int(multiplier)
        except (ValueError, TypeError):
            multiplier = 3
        products = service.get_overstock_products(
            threshold_multiplier=multiplier,
        )
        headers = ["SKU", "Product", "Category", "Reorder Point", "Total Stock", "Threshold"]
        rows = [
            [
                p.sku,
                p.name,
                str(p.category or ""),
                p.reorder_point,
                p.total_stock,
                p.reorder_point * multiplier,
            ]
            for p in products
        ]
        return multiplier, headers, rows

    def get_csv_data(self):
        _, headers, rows = self._get_export_data()
        return "overstock_report.csv", headers, rows

    def get_pdf_data(self):
        multiplier, headers, rows = self._get_export_data()
        return (
            "overstock_report.pdf",
            "Overstock Report",
            headers,
            rows,
            f"Threshold multiplier: {multiplier}x reorder point",
        )


# =====================================================================
# Purchase & Sales Summaries
# =====================================================================


class PurchaseSummaryView(CSVExportMixin, WagtailAdminTemplateMixin, TemplateView):
    """Purchase order summary grouped by time period."""

    template_name = "reports/purchase_summary.html"
    page_title = "Purchase Summary"
    header_icon = "doc-full-inverse"

    def _get_params(self):
        period = self.request.GET.get("period", "monthly")
        date_from = self.request.GET.get("date_from") or None
        date_to = self.request.GET.get("date_to") or None

        from datetime import date as date_cls
        if date_from:
            try:
                date_from = date_cls.fromisoformat(date_from)
            except ValueError:
                date_from = None
        if date_to:
            try:
                date_to = date_cls.fromisoformat(date_to)
            except ValueError:
                date_to = None

        return period, date_from, date_to

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = OrderReportService()
        period, date_from, date_to = self._get_params()

        context["summary"] = service.get_purchase_summary(
            period=period, date_from=date_from, date_to=date_to,
        )
        context["totals"] = service.get_purchase_totals(
            date_from=date_from, date_to=date_to,
        )
        context["current_period"] = period
        context["date_from"] = date_from
        context["date_to"] = date_to
        return context

    def _get_export_data(self):
        service = OrderReportService()
        period, date_from, date_to = self._get_params()
        data = service.get_purchase_summary(
            period=period, date_from=date_from, date_to=date_to,
        )
        headers = ["Period", "Order Count", "Total Cost"]
        rows = [
            [row["period"], row["order_count"], row["total_cost"]]
            for row in data
        ]
        return period, date_from, date_to, headers, rows

    def get_csv_data(self):
        _, _, _, headers, rows = self._get_export_data()
        return "purchase_summary.csv", headers, rows

    def get_pdf_data(self):
        period, date_from, date_to, headers, rows = self._get_export_data()
        subtitle_parts = [f"Grouped by: {period}"]
        if date_from:
            subtitle_parts.append(f"From: {date_from}")
        if date_to:
            subtitle_parts.append(f"To: {date_to}")
        return (
            "purchase_summary.pdf",
            "Purchase Summary",
            headers,
            rows,
            " | ".join(subtitle_parts),
        )


class SalesSummaryView(CSVExportMixin, WagtailAdminTemplateMixin, TemplateView):
    """Sales order summary grouped by time period."""

    template_name = "reports/sales_summary.html"
    page_title = "Sales Summary"
    header_icon = "doc-full-inverse"

    def _get_params(self):
        period = self.request.GET.get("period", "monthly")
        date_from = self.request.GET.get("date_from") or None
        date_to = self.request.GET.get("date_to") or None

        from datetime import date as date_cls
        if date_from:
            try:
                date_from = date_cls.fromisoformat(date_from)
            except ValueError:
                date_from = None
        if date_to:
            try:
                date_to = date_cls.fromisoformat(date_to)
            except ValueError:
                date_to = None

        return period, date_from, date_to

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = OrderReportService()
        period, date_from, date_to = self._get_params()

        context["summary"] = service.get_sales_summary(
            period=period, date_from=date_from, date_to=date_to,
        )
        context["totals"] = service.get_sales_totals(
            date_from=date_from, date_to=date_to,
        )
        context["current_period"] = period
        context["date_from"] = date_from
        context["date_to"] = date_to
        return context

    def _get_export_data(self):
        service = OrderReportService()
        period, date_from, date_to = self._get_params()
        data = service.get_sales_summary(
            period=period, date_from=date_from, date_to=date_to,
        )
        headers = ["Period", "Order Count", "Total Revenue"]
        rows = [
            [row["period"], row["order_count"], row["total_revenue"]]
            for row in data
        ]
        return period, date_from, date_to, headers, rows

    def get_csv_data(self):
        _, _, _, headers, rows = self._get_export_data()
        return "sales_summary.csv", headers, rows

    def get_pdf_data(self):
        period, date_from, date_to, headers, rows = self._get_export_data()
        subtitle_parts = [f"Grouped by: {period}"]
        if date_from:
            subtitle_parts.append(f"From: {date_from}")
        if date_to:
            subtitle_parts.append(f"To: {date_to}")
        return (
            "sales_summary.pdf",
            "Sales Summary",
            headers,
            rows,
            " | ".join(subtitle_parts),
        )
