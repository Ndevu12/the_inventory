"""Pending reservations dashboard panel."""

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from wagtail.admin.ui.components import Component

from inventory.models import StockReservation


class PendingReservationsPanel(Component):
    """Summary of pending/confirmed reservations with total count and value.

    Value is estimated from ``quantity * product.unit_cost``.
    Degrades gracefully when no reservations exist.
    """

    name = "pending_reservations"
    template_name = "inventory/panels/pending_reservations.html"
    order = 115

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)

        active_reservations = StockReservation.objects.filter(
            status__in=["pending", "confirmed"],
        )

        aggregates = active_reservations.aggregate(
            total_count=Coalesce(Sum("quantity"), 0),
            total_value=Coalesce(Sum(F("quantity") * F("product__unit_cost")), 0),
        )

        context["reservation_count"] = active_reservations.count()
        context["total_reserved_units"] = aggregates["total_count"]
        context["total_reserved_value"] = aggregates["total_value"]
        context["has_reservations"] = StockReservation.objects.exists()

        pending_count = active_reservations.filter(status="pending").count()
        confirmed_count = active_reservations.filter(status="confirmed").count()
        context["pending_count"] = pending_count
        context["confirmed_count"] = confirmed_count

        return context
