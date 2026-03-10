"""Wagtail admin dashboard panels for inventory health.

Each panel is a :class:`Component` subclass following the project's OOP
standard, rendered on the Wagtail admin homepage via the
``construct_homepage_panels`` hook.
"""

from django.db.models import F, Sum
from wagtail.admin.ui.components import Component

from inventory.models import Product, StockLocation, StockMovement, StockRecord


class StockSummaryPanel(Component):
    """At-a-glance inventory metrics.

    Displays:
    - Total active products
    - Total stock locations
    - Total items in stock (sum of all StockRecord quantities)
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
        return context


class LowStockPanel(Component):
    """Dashboard table of products below their reorder point.

    Shows up to 10 items sorted by deficit (most critical first),
    with a link to the full low-stock alerts view.
    """

    name = "low_stock"
    template_name = "inventory/panels/low_stock.html"
    order = 110

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)
        low_stock_records = (
            StockRecord.objects
            .filter(
                product__reorder_point__gt=0,
                quantity__lte=F("product__reorder_point"),
            )
            .select_related("product", "location")
            .annotate(deficit=F("product__reorder_point") - F("quantity"))
            .order_by("-deficit")[:10]
        )
        context["low_stock_records"] = low_stock_records
        return context


class RecentMovementsPanel(Component):
    """Dashboard table of the 10 most recent stock movements."""

    name = "recent_movements"
    template_name = "inventory/panels/recent_movements.html"
    order = 120

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)
        context["recent_movements"] = (
            StockMovement.objects
            .select_related("product", "from_location", "to_location")
            .order_by("-created_at")[:10]
        )
        return context
