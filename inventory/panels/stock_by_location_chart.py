"""Stock by location horizontal bar chart panel."""

import json

from django.db.models import Sum
from wagtail.admin.ui.components import Component

from inventory.models import StockLocation, StockRecord


class StockByLocationChart(Component):
    """Horizontal bar chart showing total stock quantity per active location."""

    name = "stock_by_location_chart"
    template_name = "inventory/panels/stock_by_location_chart.html"
    order = 200

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)

        location_stock = (
            StockRecord.objects.filter(location__is_active=True)
            .values("location__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("location__name")
        )

        labels = [entry["location__name"] for entry in location_stock]
        data = [entry["total_quantity"] or 0 for entry in location_stock]

        context["labels_json"] = json.dumps(labels)
        context["data_json"] = json.dumps(data)
        return context
