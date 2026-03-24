"""Dashboard API views — aggregated metrics and chart data."""

from datetime import timedelta

from django.db import models
from django.db.models import Count, F, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.context import clear_current_tenant, set_current_tenant
from tenants.middleware import resolve_tenant_for_request
from tenants.permissions import get_membership

from inventory.models import (
    Product,
    StockLocation,
    StockLot,
    StockMovement,
    StockRecord,
    StockReservation,
)
from inventory.services.cache import get_cached_dashboard, set_cached_dashboard
from procurement.models import PurchaseOrder
from reports.services.inventory_reports import InventoryReportService
from sales.models import SalesOrder


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

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if getattr(request, '_dashboard_tenant_set', False):
            clear_current_tenant()
        return response


class DashboardSummaryView(DashboardTenantScopedView):
    """High-level KPIs for the dashboard.

    Includes reservation-aware totals (reserved / available) alongside
    the original physical stock metrics.
    """

    def get(self, request):
        cached = get_cached_dashboard("summary")
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
        set_cached_dashboard("summary", data)
        return Response(data)


class StockByLocationView(DashboardTenantScopedView):
    """Stock quantity per active location with reservation breakdown.

    Returns total, reserved, and available quantities per location
    for bar/stacked-bar charts.
    """

    def get(self, request):
        cached = get_cached_dashboard("stock_by_location")
        if cached is not None:
            return Response(cached)

        reserved_subquery = (
            StockReservation.objects.filter_by_current_tenant().filter(
                location=OuterRef("location"),
                status__in=["pending", "confirmed"],
            )
            .values("location")
            .annotate(total=Sum("quantity"))
            .values("total")
        )

        qs = (
            StockRecord.objects.filter_by_current_tenant().filter(location__is_active=True)
            .values("location__name")
            .annotate(
                total_quantity=Coalesce(Sum("quantity"), 0),
                reserved=Coalesce(Subquery(reserved_subquery), 0),
            )
            .order_by("location__name")
        )

        labels = [entry["location__name"] for entry in qs]
        totals = [entry["total_quantity"] for entry in qs]
        reserved = [entry["reserved"] for entry in qs]
        available = [t - r for t, r in zip(totals, reserved)]

        data = {
            "labels": labels,
            "data": totals,
            "reserved": reserved,
            "available": available,
        }
        set_cached_dashboard("stock_by_location", data)
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
        cached = get_cached_dashboard("reservations")
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
        set_cached_dashboard("reservations", data)
        return Response(data)


class ExpiringLotsView(DashboardTenantScopedView):
    """Lots expiring within the next 30 days.

    Returns an empty list with ``has_lot_data: false`` when no lots
    exist at all, enabling graceful UI degradation.
    """

    EXPIRY_WINDOW_DAYS = 30

    def get(self, request):
        cached = get_cached_dashboard("expiring_lots")
        if cached is not None:
            return Response(cached)

        has_lot_data = StockLot.objects.filter_by_current_tenant().exists()

        if not has_lot_data:
            data = {"has_lot_data": False, "expiring_lots": []}
            set_cached_dashboard("expiring_lots", data)
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
                "product_name": lot.product.name,
                "expiry_date": lot.expiry_date.isoformat(),
                "days_to_expiry": lot.days_to_expiry(),
                "quantity_remaining": lot.quantity_remaining,
            }
            for lot in expiring_lots
        ]

        data = {"has_lot_data": True, "expiring_lots": lots_data}
        set_cached_dashboard("expiring_lots", data)
        return Response(data)
