"""Stock summary dashboard panel."""

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from wagtail.admin.ui.components import Component

from inventory.models import Product, StockLocation, StockRecord, StockReservation


class StockSummaryPanel(Component):
    """At-a-glance inventory metrics.

    Displays:
    - Total active products
    - Total stock locations
    - Total items in stock (sum of all StockRecord quantities)
    - Total reserved items (sum of active reservation quantities)
    - Total available items (total - reserved)
    - Total stock value (sum of quantity * unit_cost)
    """

    name = "stock_summary"
    template_name = "inventory/panels/stock_summary.html"
    order = 100

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)
        context["total_products"] = Product.objects.filter(is_active=True).count()
        context["total_locations"] = StockLocation.objects.filter(is_active=True).count()

        aggregates = StockRecord.objects.aggregate(
            total_items=Sum("quantity"),
            total_value=Sum(F("quantity") * F("product__unit_cost")),
        )
        context["total_items"] = aggregates["total_items"] or 0
        context["total_value"] = aggregates["total_value"] or 0

        total_reserved = StockReservation.objects.filter(
            status__in=["pending", "confirmed"],
        ).aggregate(total=Coalesce(Sum("quantity"), 0))["total"]
        context["total_reserved"] = total_reserved
        context["total_available"] = context["total_items"] - total_reserved

        return context
