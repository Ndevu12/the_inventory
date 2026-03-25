"""Report views for the Wagtail admin.

All views are read-only and follow the project's OOP standard.
Each view supports CSV export via ``?export=csv``.
"""

from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, TemplateView
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin

from inventory.models import Product, StockLocation, StockMovement
from tenants.context import get_current_tenant

from reports.exports import CSVExportMixin
from reports.filters import ExpiryReportFilter, MovementHistoryFilter
from reports.services.inventory_reports import InventoryReportService
from reports.services.order_reports import OrderReportService
from inventory.utils.warehouse_scope import report_scope_params_from_query


# =====================================================================
# Tenant verification mixin
# =====================================================================


class TenantReportMixin:
    """Mixin for report views that require tenant context."""

    def _get_current_tenant(self):
        """Get current tenant and raise PermissionDenied if not set."""
        tenant = get_current_tenant()
        if not tenant:
            raise PermissionDenied("Tenant context is not set.")
        return tenant


# =====================================================================
# Stock Valuation
# =====================================================================


class StockValuationView(
    TenantReportMixin, CSVExportMixin, WagtailAdminTemplateMixin, TemplateView
):
    """Stock valuation report with weighted-average and latest-cost methods."""

    template_name = "reports/stock_valuation.html"
    page_title = "Stock Valuation"
    header_icon = "doc-full"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self._get_current_tenant()
        service = InventoryReportService()

        method = self.request.GET.get("method", "weighted_average")
        if method not in service.VALUATION_METHODS:
            method = "weighted_average"

        scope_kw = report_scope_params_from_query(self.request.GET)
        valuations = service.get_stock_valuation(
            method=method, tenant=tenant, **scope_kw,
        )
        summary = service.get_valuation_summary(
            method=method, tenant=tenant, **scope_kw,
        )

        context["valuations"] = valuations
        context["summary"] = summary
        context["current_method"] = method
        context["methods"] = service.VALUATION_METHODS
        return context

    def _get_export_data(self):
        tenant = self._get_current_tenant()
        service = InventoryReportService()
        method = self.request.GET.get("method", "weighted_average")
        if method not in service.VALUATION_METHODS:
            method = "weighted_average"
        scope_kw = report_scope_params_from_query(self.request.GET)
        valuations = service.get_stock_valuation(
            method=method, tenant=tenant, **scope_kw,
        )
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


class MovementHistoryView(
    TenantReportMixin, CSVExportMixin, WagtailAdminTemplateMixin, ListView
):
    """Filterable, paginated movement history with audit trail."""

    template_name = "reports/movement_history.html"
    context_object_name = "movements"
    paginate_by = 50
    page_title = "Movement History"
    header_icon = "history"

    def get_queryset(self):
        tenant = self._get_current_tenant()
        qs = (
            StockMovement.objects
            .filter(tenant=tenant)
            .select_related(
                "product", "from_location", "to_location", "created_by",
            )
            .order_by("-created_at")
        )
        self.filterset = MovementHistoryFilter(
            self.request.GET,
            queryset=qs,
            tenant=tenant,
        )
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


class LowStockReportView(
    TenantReportMixin, CSVExportMixin, WagtailAdminTemplateMixin, TemplateView
):
    """Low-stock report showing products at or below their reorder point."""

    template_name = "reports/low_stock_report.html"
    page_title = "Low Stock Report"
    header_icon = "warning"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self._get_current_tenant()
        service = InventoryReportService()
        scope_kw = report_scope_params_from_query(self.request.GET)
        context["products"] = service.get_low_stock_products(tenant=tenant, **scope_kw)
        context["total_count"] = context["products"].count()
        return context

    def _get_export_data(self):
        tenant = self._get_current_tenant()
        service = InventoryReportService()
        scope_kw = report_scope_params_from_query(self.request.GET)
        products = service.get_low_stock_products(tenant=tenant, **scope_kw)
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


class OverstockReportView(
    TenantReportMixin, CSVExportMixin, WagtailAdminTemplateMixin, TemplateView
):
    """Overstock report showing products with excessive inventory."""

    template_name = "reports/overstock_report.html"
    page_title = "Overstock Report"
    header_icon = "plus-inverse"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self._get_current_tenant()
        service = InventoryReportService()

        multiplier = self.request.GET.get("threshold", 3)
        try:
            multiplier = int(multiplier)
        except (ValueError, TypeError):
            multiplier = 3

        scope_kw = report_scope_params_from_query(self.request.GET)
        products = service.get_overstock_products(
            threshold_multiplier=multiplier, tenant=tenant, **scope_kw,
        )
        context["products"] = products
        context["total_count"] = products.count()
        context["threshold_multiplier"] = multiplier
        return context

    def _get_export_data(self):
        tenant = self._get_current_tenant()
        service = InventoryReportService()
        multiplier = self.request.GET.get("threshold", 3)
        try:
            multiplier = int(multiplier)
        except (ValueError, TypeError):
            multiplier = 3
        scope_kw = report_scope_params_from_query(self.request.GET)
        products = service.get_overstock_products(
            threshold_multiplier=multiplier, tenant=tenant, **scope_kw,
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
# Lot Expiry
# =====================================================================


class ExpiryReportView(
    TenantReportMixin, CSVExportMixin, WagtailAdminTemplateMixin, TemplateView
):
    """Lots approaching or past their expiry date."""

    template_name = "reports/expiry_report.html"
    page_title = "Product Expiry Report"
    header_icon = "time"

    def _get_params(self):
        tenant = self._get_current_tenant()
        days_ahead = self.request.GET.get("days_ahead", "30")
        try:
            days_ahead = max(1, int(days_ahead))
        except (ValueError, TypeError):
            days_ahead = 30

        product_id = self.request.GET.get("product") or None
        location_id = self.request.GET.get("location") or None

        product = None
        location = None
        if product_id:
            try:
                product = Product.objects.filter(tenant=tenant).get(pk=product_id)
            except (Product.DoesNotExist, ValueError):
                pass
        if location_id:
            try:
                location = StockLocation.objects.filter(
                    tenant=tenant,
                ).get(pk=location_id)
            except (StockLocation.DoesNotExist, ValueError):
                pass

        return days_ahead, product, location, tenant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self._get_current_tenant()
        service = InventoryReportService()
        days_ahead, product, location, _ = self._get_params()
        scope_kw = report_scope_params_from_query(self.request.GET)

        expiring = service.get_expiring_lots(
            days_ahead=days_ahead,
            product=product,
            location=location,
            tenant=tenant,
            **scope_kw,
        )
        expired = service.get_expired_lots(
            product=product,
            location=location,
            tenant=tenant,
            **scope_kw,
        )

        self.filterset = ExpiryReportFilter(self.request.GET, queryset=expiring)

        context["expiring_lots"] = expiring
        context["expired_lots"] = expired
        context["days_ahead"] = days_ahead
        context["expiring_count"] = expiring.count()
        context["expired_count"] = expired.count()
        context["filterset"] = self.filterset
        return context

    def _get_export_data(self):
        service = InventoryReportService()
        days_ahead, product, location, tenant = self._get_params()
        scope_kw = report_scope_params_from_query(self.request.GET)
        expiring = service.get_expiring_lots(
            days_ahead=days_ahead,
            product=product,
            location=location,
            tenant=tenant,
            **scope_kw,
        )
        expired = service.get_expired_lots(
            product=product,
            location=location,
            tenant=tenant,
            **scope_kw,
        )
        headers = [
            "Status", "SKU", "Product", "Lot Number", "Expiry Date",
            "Days Left", "Qty Remaining", "Qty Received", "Supplier",
        ]
        rows = []
        for lot in expired:
            rows.append([
                "EXPIRED", lot.product.sku, lot.product.name,
                lot.lot_number, lot.expiry_date, lot.days_to_expiry(),
                lot.quantity_remaining, lot.quantity_received,
                str(lot.supplier or ""),
            ])
        for lot in expiring:
            rows.append([
                "EXPIRING", lot.product.sku, lot.product.name,
                lot.lot_number, lot.expiry_date, lot.days_to_expiry(),
                lot.quantity_remaining, lot.quantity_received,
                str(lot.supplier or ""),
            ])
        return days_ahead, headers, rows

    def get_csv_data(self):
        days_ahead, headers, rows = self._get_export_data()
        return f"expiry_report_{days_ahead}d.csv", headers, rows

    def get_pdf_data(self):
        days_ahead, headers, rows = self._get_export_data()
        return (
            f"expiry_report_{days_ahead}d.pdf",
            "Product Expiry Report",
            headers,
            rows,
            f"Look-ahead: {days_ahead} days | {len(rows)} lot(s)",
        )


# =====================================================================
# Purchase & Sales Summaries
# =====================================================================


class PurchaseSummaryView(
    TenantReportMixin, CSVExportMixin, WagtailAdminTemplateMixin, TemplateView
):
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
        tenant = self._get_current_tenant()
        service = OrderReportService()
        period, date_from, date_to = self._get_params()

        scope_kw = report_scope_params_from_query(self.request.GET)
        context["summary"] = service.get_purchase_summary(
            tenant=tenant,
            period=period,
            date_from=date_from,
            date_to=date_to,
            **scope_kw,
        )
        context["totals"] = service.get_purchase_totals(
            tenant=tenant,
            date_from=date_from,
            date_to=date_to,
            **scope_kw,
        )
        context["current_period"] = period
        context["date_from"] = date_from
        context["date_to"] = date_to
        return context

    def _get_export_data(self):
        tenant = self._get_current_tenant()
        service = OrderReportService()
        period, date_from, date_to = self._get_params()
        scope_kw = report_scope_params_from_query(self.request.GET)
        data = service.get_purchase_summary(
            tenant=tenant,
            period=period,
            date_from=date_from,
            date_to=date_to,
            **scope_kw,
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


class SalesSummaryView(
    TenantReportMixin, CSVExportMixin, WagtailAdminTemplateMixin, TemplateView
):
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
        tenant = self._get_current_tenant()
        service = OrderReportService()
        period, date_from, date_to = self._get_params()

        scope_kw = report_scope_params_from_query(self.request.GET)
        context["summary"] = service.get_sales_summary(
            tenant=tenant,
            period=period,
            date_from=date_from,
            date_to=date_to,
            **scope_kw,
        )
        context["totals"] = service.get_sales_totals(
            tenant=tenant,
            date_from=date_from,
            date_to=date_to,
            **scope_kw,
        )
        context["current_period"] = period
        context["date_from"] = date_from
        context["date_to"] = date_to
        return context

    def _get_export_data(self):
        tenant = self._get_current_tenant()
        service = OrderReportService()
        period, date_from, date_to = self._get_params()
        scope_kw = report_scope_params_from_query(self.request.GET)
        data = service.get_sales_summary(
            tenant=tenant,
            period=period,
            date_from=date_from,
            date_to=date_to,
            **scope_kw,
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
