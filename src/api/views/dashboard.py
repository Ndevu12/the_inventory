"""Dashboard API views — aggregated metrics and chart data."""

from datetime import timedelta

from django.db import models
from django.db.models import Count, F, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone, translation
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.context import clear_current_tenant, get_current_tenant, set_current_tenant
from tenants.middleware import resolve_tenant_for_request
from tenants.permissions import get_membership

from inventory.models import (
    Product,
    StockLocation,
    StockLot,
    StockMovement,
    StockRecord,
    StockReservation,
    Warehouse,
)
from inventory.services.cache import get_cached_dashboard, set_cached_dashboard
from inventory.utils.localized_attributes import attribute_in_display_locale
from procurement.models import PurchaseOrder
from reports.services.inventory_reports import InventoryReportService
from sales.models import SalesOrder

from api.language import resolve_display_language_code, wagtail_locale_for_language


class DashboardTenantScopedView(APIView):
    """Resolve tenant after DRF auth and set thread-local context.

    ``TenantMiddleware`` runs before JWT authentication, so
    ``get_current_tenant()`` is often unset for API requests. Dashboard
    code (report services, cache keys, ``filter_by_current_tenant()``)
    needs the active tenant for the full request.
    """

    permission_classes = (IsAuthenticated,)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        tenant = resolve_tenant_for_request(request)
        if tenant is None:
            raise PermissionDenied("No tenant context available.")
        if not get_membership(request.user, tenant):
            raise PermissionDenied("User does not belong to this tenant.")
        set_current_tenant(tenant)
        request._dashboard_tenant_set = True
        display_code = resolve_display_language_code(request, tenant)
        self._dashboard_language_code = display_code
        self._dashboard_display_locale = wagtail_locale_for_language(display_code)
        translation.activate(display_code)

    def finalize_response(self, request, response, *args, **kwargs):
        try:
            return super().finalize_response(request, response, *args, **kwargs)
        finally:
            translation.deactivate()
            if getattr(request, "_dashboard_tenant_set", False):
                clear_current_tenant()


class DashboardSummaryView(DashboardTenantScopedView):
    """High-level KPIs for the dashboard.

    Includes reservation-aware totals (reserved / available) alongside
    the original physical stock metrics.
    """

    def get(self, request):
        lang = self._dashboard_language_code
        cached = get_cached_dashboard("summary", language_code=lang)
        if cached is not None:
            return Response(cached)

        report_service = InventoryReportService()
        reserved_stock_value = report_service.get_reserved_stock_value()

        total_items = StockRecord.objects.filter_by_current_tenant().aggregate(
            total=Coalesce(Sum("quantity"), 0),
        )["total"]

        total_reserved = StockReservation.objects.filter_by_current_tenant().filter(
            status__in=["pending", "confirmed"],
        ).aggregate(total=Coalesce(Sum("quantity"), 0))["total"]

        data = {
            "total_products": Product.objects.filter_by_current_tenant().filter(
                is_active=True,
            ).count(),
            "total_locations": StockLocation.objects.filter_by_current_tenant().filter(
                is_active=True,
            ).count(),
            "active_warehouses": Warehouse.objects.filter_by_current_tenant().filter(
                is_active=True,
            ).count(),
            "locations_with_warehouse": StockLocation.objects.filter_by_current_tenant().filter(
                is_active=True,
                warehouse__isnull=False,
            ).count(),
            "locations_retail_site": StockLocation.objects.filter_by_current_tenant().filter(
                is_active=True,
                warehouse__isnull=True,
            ).count(),
            "low_stock_count": Product.objects.filter_by_current_tenant().filter(
                is_active=True,
            ).low_stock().count(),
            "total_stock_records": StockRecord.objects.filter_by_current_tenant().count(),
            "total_reserved": total_reserved,
            "total_available": total_items - total_reserved,
            "purchase_orders": PurchaseOrder.objects.filter_by_current_tenant().count(),
            "sales_orders": SalesOrder.objects.filter_by_current_tenant().count(),
            "reserved_stock_value": str(reserved_stock_value),
        }
        set_cached_dashboard("summary", data, language_code=lang)
        return Response(data)


class StockByLocationView(DashboardTenantScopedView):
    """Stock quantity per active location with reservation breakdown.

    Returns total, reserved, and available quantities per location
    for bar/stacked-bar charts.
    """

    def get(self, request):
        lang = self._dashboard_language_code
        cached = get_cached_dashboard("stock_by_location", language_code=lang)
        if cached is not None:
            return Response(cached)

        reserved_subquery = (
            StockReservation.objects.filter_by_current_tenant().filter(
                location_id=OuterRef("location_id"),
                status__in=["pending", "confirmed"],
            )
            .values("location_id")
            .annotate(total=Sum("quantity"))
            .values("total")
        )

        qs = (
            StockRecord.objects.filter_by_current_tenant().filter(location__is_active=True)
            .values("location_id")
            .annotate(
                total_quantity=Coalesce(Sum("quantity"), 0),
                reserved=Coalesce(Subquery(reserved_subquery), 0),
            )
        )

        entries = list(qs)
        loc_ids = [e["location_id"] for e in entries if e.get("location_id") is not None]
        display_loc = self._dashboard_display_locale
        locations_by_id = {
            loc.pk: loc
            for loc in StockLocation.objects.filter(pk__in=loc_ids).select_related(
                "warehouse",
            )
        }

        def _location_chart_label(location_id):
            loc = locations_by_id.get(location_id)
            if loc is None:
                return ""
            name = attribute_in_display_locale(loc, "name", display_loc) or ""
            if loc.warehouse_id and loc.warehouse:
                wh_name = (loc.warehouse.name or "").strip()
                if wh_name:
                    return f"{wh_name} › {name}"
            return name

        ordered = sorted(entries, key=lambda e: _location_chart_label(e["location_id"]))
        labels = [_location_chart_label(e["location_id"]) for e in ordered]
        totals = [e["total_quantity"] for e in ordered]
        reserved = [e["reserved"] for e in ordered]
        available = [t - r for t, r in zip(totals, reserved)]

        tenant = get_current_tenant()
        retail_site_label = (
            ((tenant.branding_site_name or "").strip() or tenant.name)
            if tenant
            else "Store"
        )

        stock_site_qs = (
            StockRecord.objects.filter_by_current_tenant()
            .filter(location__is_active=True)
            .values("location__warehouse_id", "location__warehouse__name")
            .annotate(total_quantity=Coalesce(Sum("quantity"), 0))
        )
        res_site_qs = (
            StockReservation.objects.filter_by_current_tenant()
            .filter(
                status__in=["pending", "confirmed"],
                location__is_active=True,
            )
            .values("location__warehouse_id", "location__warehouse__name")
            .annotate(res_site_reserved=Coalesce(Sum("quantity"), 0))
        )

        site_buckets: dict[int | None, dict] = {}
        for row in stock_site_qs:
            wid = row["location__warehouse_id"]
            site_buckets.setdefault(
                wid,
                {
                    "warehouse_id": wid,
                    "label": (
                        row["location__warehouse__name"]
                        if wid is not None
                        else retail_site_label
                    ),
                    "kind": "warehouse" if wid is not None else "retail_site",
                    "total_quantity": 0,
                    "reserved": 0,
                },
            )
            site_buckets[wid]["total_quantity"] = row["total_quantity"]

        for row in res_site_qs:
            wid = row["location__warehouse_id"]
            site_buckets.setdefault(
                wid,
                {
                    "warehouse_id": wid,
                    "label": (
                        row["location__warehouse__name"]
                        if wid is not None
                        else retail_site_label
                    ),
                    "kind": "warehouse" if wid is not None else "retail_site",
                    "total_quantity": 0,
                    "reserved": 0,
                },
            )
            site_buckets[wid]["reserved"] = row["res_site_reserved"]

        by_site = []
        for wid in sorted(site_buckets.keys(), key=lambda k: (k is None, site_buckets[k]["label"])):
            b = site_buckets[wid]
            tq = b["total_quantity"]
            rv = b["reserved"]
            by_site.append({
                "warehouse_id": wid,
                "label": b["label"],
                "kind": b["kind"],
                "total_quantity": tq,
                "reserved": rv,
                "available": tq - rv,
            })

        data = {
            "labels": labels,
            "data": totals,
            "reserved": reserved,
            "available": available,
            "by_site": by_site,
        }
        set_cached_dashboard("stock_by_location", data, language_code=lang)
        return Response(data)


class MovementTrendsView(DashboardTenantScopedView):
    """Daily movement count for the last 30 days — for line charts."""

    def get(self, request):
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        qs = (
            StockMovement.objects.filter_by_current_tenant().filter(
                created_at__date__gte=thirty_days_ago,
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        counts_by_date = {entry["date"]: entry["count"] for entry in qs}

        labels = []
        data = []
        for i in range(31):
            day = thirty_days_ago + timedelta(days=i)
            labels.append(day.strftime("%Y-%m-%d"))
            data.append(counts_by_date.get(day, 0))

        return Response({"labels": labels, "data": data})


class OrderStatusView(DashboardTenantScopedView):
    """Purchase and sales order counts by status — for doughnut charts."""

    def get(self, request):
        po_qs = (
            PurchaseOrder.objects.filter_by_current_tenant().values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        so_qs = (
            SalesOrder.objects.filter_by_current_tenant().values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        return Response({
            "purchase_orders": {
                "labels": [e["status"].capitalize() for e in po_qs],
                "data": [e["count"] for e in po_qs],
            },
            "sales_orders": {
                "labels": [e["status"].capitalize() for e in so_qs],
                "data": [e["count"] for e in so_qs],
            },
        })


class PendingReservationsView(DashboardTenantScopedView):
    """Pending and confirmed reservation summary — count, units, and value."""

    def get(self, request):
        lang = self._dashboard_language_code
        cached = get_cached_dashboard("reservations", language_code=lang)
        if cached is not None:
            return Response(cached)

        active_qs = StockReservation.objects.filter_by_current_tenant().filter(
            status__in=["pending", "confirmed"],
        )

        aggregates = active_qs.aggregate(
            total_units=Coalesce(Sum("quantity"), 0),
            total_value=Coalesce(
                Sum(F("quantity") * F("product__unit_cost")),
                0,
                output_field=models.DecimalField(),
            ),
        )

        by_status = (
            active_qs.values("status")
            .annotate(
                count=Count("id"),
                units=Coalesce(Sum("quantity"), 0),
            )
            .order_by("status")
        )

        breakdown = {
            entry["status"]: {"count": entry["count"], "units": entry["units"]}
            for entry in by_status
        }

        data = {
            "reservation_count": active_qs.count(),
            "total_units": aggregates["total_units"],
            "total_value": float(aggregates["total_value"]),
            "pending": breakdown.get("pending", {"count": 0, "units": 0}),
            "confirmed": breakdown.get("confirmed", {"count": 0, "units": 0}),
        }
        set_cached_dashboard("reservations", data, language_code=lang)
        return Response(data)


class ExpiringLotsView(DashboardTenantScopedView):
    """Lots expiring within the next 30 days.

    Returns an empty list with ``has_lot_data: false`` when no lots
    exist at all, enabling graceful UI degradation.
    """

    EXPIRY_WINDOW_DAYS = 30

    def get(self, request):
        lang = self._dashboard_language_code
        display_locale = self._dashboard_display_locale
        cached = get_cached_dashboard("expiring_lots", language_code=lang)
        if cached is not None:
            return Response(cached)

        has_lot_data = StockLot.objects.filter_by_current_tenant().exists()

        if not has_lot_data:
            data = {"has_lot_data": False, "expiring_lots": []}
            set_cached_dashboard("expiring_lots", data, language_code=lang)
            return Response(data)

        today = timezone.now().date()
        cutoff = today + timedelta(days=self.EXPIRY_WINDOW_DAYS)

        expiring_lots = (
            StockLot.objects.filter_by_current_tenant()
            .filter(
                is_active=True,
                expiry_date__isnull=False,
                expiry_date__lte=cutoff,
                quantity_remaining__gt=0,
            )
            .select_related("product")
            .order_by("expiry_date")[:20]
        )

        lots_data = [
            {
                "id": lot.pk,
                "lot_number": lot.lot_number,
                "product_sku": lot.product.sku,
                "product_name": attribute_in_display_locale(
                    lot.product, "name", display_locale,
                ),
                "expiry_date": lot.expiry_date.isoformat(),
                "days_to_expiry": lot.days_to_expiry(),
                "quantity_remaining": lot.quantity_remaining,
            }
            for lot in expiring_lots
        ]

        data = {"has_lot_data": True, "expiring_lots": lots_data}
        set_cached_dashboard("expiring_lots", data, language_code=lang)
        return Response(data)
