"""Recent stock movements dashboard panel."""

from wagtail.admin.ui.components import Component

from inventory.models import StockMovement


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
