"""Dashboard API views — aggregated metrics and chart data."""

from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import Product, StockLocation, StockMovement, StockRecord
from procurement.models import PurchaseOrder
from sales.models import SalesOrder


class DashboardSummaryView(APIView):
    """High-level KPIs for the dashboard."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response({
            "total_products": Product.objects.filter(is_active=True).count(),
            "total_locations": StockLocation.objects.filter(is_active=True).count(),
            "low_stock_count": Product.objects.filter(is_active=True).low_stock().count(),
            "total_stock_records": StockRecord.objects.count(),
            "purchase_orders": PurchaseOrder.objects.count(),
            "sales_orders": SalesOrder.objects.count(),
        })


class StockByLocationView(APIView):
    """Total stock quantity per active location — for bar charts."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        qs = (
            StockRecord.objects.filter(location__is_active=True)
            .values("location__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("location__name")
        )
        labels = [entry["location__name"] for entry in qs]
        data = [entry["total_quantity"] or 0 for entry in qs]
        return Response({"labels": labels, "data": data})


class MovementTrendsView(APIView):
    """Daily movement count for the last 30 days — for line charts."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        qs = (
            StockMovement.objects.filter(created_at__date__gte=thirty_days_ago)
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


class OrderStatusView(APIView):
    """Purchase and sales order counts by status — for doughnut charts."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        po_qs = (
            PurchaseOrder.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        so_qs = (
            SalesOrder.objects.values("status")
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
