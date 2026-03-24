"""Low-stock items dashboard panel."""

from django.db.models import F, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from wagtail.admin.ui.components import Component

from inventory.models import StockRecord, StockReservation


class LowStockPanel(Component):
    """Dashboard table of products below their reorder point.

    Uses reservation-aware available quantity so that reserved stock is
    not counted as available when evaluating reorder thresholds.

    Shows up to 10 items sorted by deficit (most critical first),
    with a link to the full low-stock alerts view.
    """

    name = "low_stock"
    template_name = "inventory/panels/low_stock.html"
    order = 110

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)

        reserved_subquery = (
            StockReservation.objects.filter(
                product=OuterRef("product"),
                location=OuterRef("location"),
                status__in=["pending", "confirmed"],
            )
            .values("product", "location")
            .annotate(total=Sum("quantity"))
            .values("total")
        )

        low_stock_records = (
            StockRecord.objects
            .annotate(
                reserved_qty=Coalesce(Subquery(reserved_subquery), 0),
                available_qty=F("quantity") - F("reserved_qty"),
            )
            .filter(
                product__reorder_point__gt=0,
                available_qty__lte=F("product__reorder_point"),
            )
            .select_related("product", "location")
            .annotate(deficit=F("product__reorder_point") - F("available_qty"))
            .order_by("-deficit")[:10]
        )
        context["low_stock_records"] = low_stock_records
        return context
