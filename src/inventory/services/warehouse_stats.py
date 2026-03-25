"""Aggregated metrics per warehouse (facility) for tenant ops dashboards."""

from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from inventory.models import StockLocation, StockRecord, Warehouse
from inventory.models.reservation import ReservationStatus, StockReservation

_ACTIVE_RESERVATION_STATUSES = (
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
)


def warehouses_with_quick_stats(*, tenant):
    """Return warehouses for *tenant* annotated with per-facility aggregates (one query).

    Metrics align with :meth:`inventory.models.stock.StockRecord.is_low_stock`
    (reservation-aware available vs product reorder point).
    """
    tid = tenant.pk if tenant is not None else None
    if tid is None:
        return Warehouse.objects.none()

    on_hand = Coalesce(
        Subquery(
            StockRecord.objects.filter(
                tenant_id=tid,
                location__warehouse_id=OuterRef("pk"),
            )
            .values("location__warehouse_id")
            .annotate(total=Sum("quantity"))
            .values("total")[:1],
            output_field=IntegerField(),
        ),
        Value(0),
        output_field=IntegerField(),
    )

    reserved_qty = Coalesce(
        Subquery(
            StockReservation.objects.filter(
                tenant_id=tid,
                location__warehouse_id=OuterRef("pk"),
                status__in=_ACTIVE_RESERVATION_STATUSES,
            )
            .values("location__warehouse_id")
            .annotate(total=Sum("quantity"))
            .values("total")[:1],
            output_field=IntegerField(),
        ),
        Value(0),
        output_field=IntegerField(),
    )

    capacity_total = Coalesce(
        Subquery(
            StockLocation.objects.filter(
                tenant_id=tid,
                warehouse_id=OuterRef("pk"),
                max_capacity__isnull=False,
            )
            .values("warehouse_id")
            .annotate(total=Sum("max_capacity"))
            .values("total")[:1],
            output_field=IntegerField(),
        ),
        Value(0),
        output_field=IntegerField(),
    )

    reserved_line = Coalesce(
        Subquery(
            StockReservation.objects.filter(
                tenant_id=tid,
                product_id=OuterRef("product_id"),
                location_id=OuterRef("location_id"),
                status__in=_ACTIVE_RESERVATION_STATUSES,
            )
            .order_by()
            .values("product_id")
            .annotate(line_reserved=Sum("quantity"))
            .values("line_reserved")[:1],
            output_field=IntegerField(),
        ),
        Value(0),
        output_field=IntegerField(),
    )

    low_stock_lines = Coalesce(
        Subquery(
            StockRecord.objects.filter(
                tenant_id=tid,
                location__warehouse_id=OuterRef("pk"),
            )
            .annotate(reserved_at_line=reserved_line)
            .annotate(
                available=ExpressionWrapper(
                    F("quantity") - F("reserved_at_line"),
                    output_field=IntegerField(),
                ),
            )
            .filter(available__lte=F("product__reorder_point"))
            .values("location__warehouse_id")
            .annotate(c=Count("pk", distinct=True))
            .values("c")[:1],
            output_field=IntegerField(),
        ),
        Value(0),
        output_field=IntegerField(),
    )

    return (
        Warehouse.objects.filter(tenant_id=tid)
        .annotate(
            location_count=Count(
                "stock_locations",
                filter=Q(stock_locations__is_active=True),
                distinct=True,
            ),
            total_on_hand=on_hand,
            reserved_quantity=reserved_qty,
            capacity_total=capacity_total,
            low_stock_line_count=low_stock_lines,
        )
        .order_by("name")
    )

