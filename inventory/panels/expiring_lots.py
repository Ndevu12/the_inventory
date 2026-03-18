"""Expiring lots dashboard panel."""

from datetime import timedelta

from django.utils import timezone
from wagtail.admin.ui.components import Component

from inventory.models import StockLot


class ExpiringLotsPanel(Component):
    """Dashboard table of lots expiring within the next 30 days.

    Only shown when lot data exists; otherwise displays a "no expiring lots"
    message for graceful degradation.
    """

    name = "expiring_lots"
    template_name = "inventory/panels/expiring_lots.html"
    order = 120

    EXPIRY_WINDOW_DAYS = 30

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)

        today = timezone.now().date()
        cutoff = today + timedelta(days=self.EXPIRY_WINDOW_DAYS)

        expiring_lots = (
            StockLot.objects
            .filter(
                is_active=True,
                expiry_date__isnull=False,
                expiry_date__lte=cutoff,
                quantity_remaining__gt=0,
            )
            .select_related("product")
            .order_by("expiry_date")[:10]
        )

        context["expiring_lots"] = expiring_lots
        context["has_lot_data"] = StockLot.objects.exists()
        return context
