"""Order reporting service for procurement and sales analytics.

Provides read-only aggregations over purchase orders and sales orders,
with support for period-based grouping (daily, weekly, monthly).
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncWeek

from inventory.utils.warehouse_scope import (
    WAREHOUSE_SCOPE_UNSPECIFIED,
    parse_report_warehouse_scope,
)
from procurement.models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from sales.models import SalesOrder, SalesOrderLine, SalesOrderStatus
from tenants.context import get_current_tenant

if TYPE_CHECKING:
    from tenants.models import Tenant


TRUNC_FUNCTIONS = {
    "daily": TruncDay,
    "weekly": TruncWeek,
    "monthly": TruncMonth,
}


class OrderReportService:
    """Read-only reporting on purchase and sales order activity.

    Usage::

        service = OrderReportService()
        purchase_data = service.get_purchase_summary(period="monthly")
        sales_data =         service.get_sales_summary(period="monthly")
    """

    @staticmethod
    def _scoped_purchase_orders(
        qs,
        *,
        scope: str,
        warehouse_id: int | None,
    ):
        if scope == "all":
            return qs
        if scope == "retail":
            return qs.filter(
                goods_received_notes__location__warehouse_id__isnull=True,
            ).distinct()
        return qs.filter(
            goods_received_notes__location__warehouse_id=warehouse_id,
        ).distinct()

    @staticmethod
    def _scoped_sales_orders(
        qs,
        *,
        scope: str,
        warehouse_id: int | None,
    ):
        if scope == "all":
            return qs
        if scope == "retail":
            return qs.filter(
                dispatches__from_location__warehouse_id__isnull=True,
            ).distinct()
        return qs.filter(
            dispatches__from_location__warehouse_id=warehouse_id,
        ).distinct()

    # ------------------------------------------------------------------
    # Purchase Order Reports
    # ------------------------------------------------------------------

    def get_purchase_summary(
        self,
        *,
        tenant: Tenant | None = None,
        period: str = "monthly",
        date_from: date | None = None,
        date_to: date | None = None,
        warehouse_id: int | None | object = WAREHOUSE_SCOPE_UNSPECIFIED,
        retail_locations_only: bool = False,
    ) -> list[dict]:
        """Aggregate purchase orders by time period.

        Returns a list of dicts with ``period``, ``order_count``, and
        ``total_cost`` for each time bucket.

        Parameters
        ----------
        tenant : Tenant | None
            Tenant to filter by. Defaults to current tenant from context.
        period : str
            ``"daily"``, ``"weekly"``, or ``"monthly"``.
        date_from, date_to : date | None
            Optional date range filter on ``order_date``.
        """
        tenant = tenant or get_current_tenant()
        if not tenant:
            raise ValueError("No tenant provided or found in context")

        trunc_fn = self._get_trunc_function(period)
        scope, wid = parse_report_warehouse_scope(
            warehouse_id=warehouse_id,
            retail_locations_only=retail_locations_only,
        )

        qs = PurchaseOrder.objects.filter(tenant=tenant).exclude(
            status=PurchaseOrderStatus.CANCELLED,
        )
        qs = self._apply_date_filter(qs, "order_date", date_from, date_to)
        qs = self._scoped_purchase_orders(qs, scope=scope, warehouse_id=wid)

        return list(
            qs
            .annotate(period=trunc_fn("order_date"))
            .values("period")
            .annotate(
                order_count=Count("id"),
                total_cost=Coalesce(
                    Sum(
                        F("lines__quantity") * F("lines__unit_cost"),
                        output_field=DecimalField(),
                    ),
                    0,
                    output_field=DecimalField(),
                ),
            )
            .order_by("period")
        )

    def get_purchase_totals(
        self,
        *,
        tenant: Tenant | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        warehouse_id: int | None | object = WAREHOUSE_SCOPE_UNSPECIFIED,
        retail_locations_only: bool = False,
    ) -> dict:
        """Aggregate totals for purchase orders (non-cancelled).

        Returns ``order_count``, ``line_count``, ``total_cost``,
        and ``status_breakdown``.
        """
        tenant = tenant or get_current_tenant()
        if not tenant:
            raise ValueError("No tenant provided or found in context")
        scope, wid = parse_report_warehouse_scope(
            warehouse_id=warehouse_id,
            retail_locations_only=retail_locations_only,
        )

        qs = PurchaseOrder.objects.filter(tenant=tenant).exclude(
            status=PurchaseOrderStatus.CANCELLED,
        )
        qs = self._apply_date_filter(qs, "order_date", date_from, date_to)
        qs = self._scoped_purchase_orders(qs, scope=scope, warehouse_id=wid)

        order_count = qs.count()

        line_agg = PurchaseOrderLine.objects.filter(
            purchase_order__in=qs,
        ).aggregate(
            line_count=Count("id"),
            total_cost=Coalesce(
                Sum(
                    F("quantity") * F("unit_cost"),
                    output_field=DecimalField(),
                ),
                0,
                output_field=DecimalField(),
            ),
        )

        status_breakdown = dict(
            qs.values_list("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        return {
            "order_count": order_count,
            "line_count": line_agg["line_count"],
            "total_cost": line_agg["total_cost"],
            "status_breakdown": status_breakdown,
        }

    # ------------------------------------------------------------------
    # Sales Order Reports
    # ------------------------------------------------------------------

    def get_sales_summary(
        self,
        *,
        tenant: Tenant | None = None,
        period: str = "monthly",
        date_from: date | None = None,
        date_to: date | None = None,
        warehouse_id: int | None | object = WAREHOUSE_SCOPE_UNSPECIFIED,
        retail_locations_only: bool = False,
    ) -> list[dict]:
        """Aggregate sales orders by time period.

        Returns a list of dicts with ``period``, ``order_count``, and
        ``total_revenue`` for each time bucket.
        """
        tenant = tenant or get_current_tenant()
        if not tenant:
            raise ValueError("No tenant provided or found in context")

        trunc_fn = self._get_trunc_function(period)
        scope, wid = parse_report_warehouse_scope(
            warehouse_id=warehouse_id,
            retail_locations_only=retail_locations_only,
        )

        qs = SalesOrder.objects.filter(tenant=tenant).exclude(
            status=SalesOrderStatus.CANCELLED,
        )
        qs = self._apply_date_filter(qs, "order_date", date_from, date_to)
        qs = self._scoped_sales_orders(qs, scope=scope, warehouse_id=wid)

        return list(
            qs
            .annotate(period=trunc_fn("order_date"))
            .values("period")
            .annotate(
                order_count=Count("id"),
                total_revenue=Coalesce(
                    Sum(
                        F("lines__quantity") * F("lines__unit_price"),
                        output_field=DecimalField(),
                    ),
                    0,
                    output_field=DecimalField(),
                ),
            )
            .order_by("period")
        )

    def get_sales_totals(
        self,
        *,
        tenant: Tenant | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        warehouse_id: int | None | object = WAREHOUSE_SCOPE_UNSPECIFIED,
        retail_locations_only: bool = False,
    ) -> dict:
        """Aggregate totals for sales orders (non-cancelled).

        Returns ``order_count``, ``line_count``, ``total_revenue``,
        and ``status_breakdown``.
        """
        tenant = tenant or get_current_tenant()
        if not tenant:
            raise ValueError("No tenant provided or found in context")
        scope, wid = parse_report_warehouse_scope(
            warehouse_id=warehouse_id,
            retail_locations_only=retail_locations_only,
        )

        qs = SalesOrder.objects.filter(tenant=tenant).exclude(
            status=SalesOrderStatus.CANCELLED,
        )
        qs = self._apply_date_filter(qs, "order_date", date_from, date_to)
        qs = self._scoped_sales_orders(qs, scope=scope, warehouse_id=wid)

        order_count = qs.count()

        line_agg = SalesOrderLine.objects.filter(
            sales_order__in=qs,
        ).aggregate(
            line_count=Count("id"),
            total_revenue=Coalesce(
                Sum(
                    F("quantity") * F("unit_price"),
                    output_field=DecimalField(),
                ),
                0,
                output_field=DecimalField(),
            ),
        )

        status_breakdown = dict(
            qs.values_list("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        return {
            "order_count": order_count,
            "line_count": line_agg["line_count"],
            "total_revenue": line_agg["total_revenue"],
            "status_breakdown": status_breakdown,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_trunc_function(self, period: str):
        fn = TRUNC_FUNCTIONS.get(period)
        if fn is None:
            raise ValueError(
                f"Unknown period '{period}'. "
                f"Choose from: {', '.join(TRUNC_FUNCTIONS)}"
            )
        return fn

    @staticmethod
    def _apply_date_filter(qs, field_name, date_from, date_to):
        if date_from:
            qs = qs.filter(**{f"{field_name}__gte": date_from})
        if date_to:
            qs = qs.filter(**{f"{field_name}__lte": date_to})
        return qs
