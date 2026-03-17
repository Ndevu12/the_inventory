"""Order status doughnut charts panel."""

import json

from django.db.models import Count
from wagtail.admin.ui.components import Component

from procurement.models import PurchaseOrder
from sales.models import SalesOrder


class OrderStatusChart(Component):
    """Two side-by-side doughnut charts for purchase and sales order statuses."""

    name = "order_status_chart"
    template_name = "inventory/panels/order_status_chart.html"
    order = 220

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)

        po_statuses = (
            PurchaseOrder.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        context["po_labels_json"] = json.dumps(
            [entry["status"].capitalize() for entry in po_statuses]
        )
        context["po_data_json"] = json.dumps(
            [entry["count"] for entry in po_statuses]
        )

        so_statuses = (
            SalesOrder.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        context["so_labels_json"] = json.dumps(
            [entry["status"].capitalize() for entry in so_statuses]
        )
        context["so_data_json"] = json.dumps(
            [entry["count"] for entry in so_statuses]
        )

        return context
