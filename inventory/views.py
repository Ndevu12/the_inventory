"""Inventory views for the Wagtail admin.

All views follow the project's OOP standard — class-based with
WagtailAdminTemplateMixin for consistent admin chrome.
"""

from django.views.generic import ListView
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin

from inventory.filters import ProductFilterSet
from inventory.models import Product


class LowStockAlertView(WagtailAdminTemplateMixin, ListView):
    """Display products that are at or below their reorder point.

    Integrates with the Wagtail admin shell (header, breadcrumbs, sidebar
    highlight) and uses :class:`ProductFilterSet` for filtering by
    category, stock status, location, and active state.
    """

    template_name = "inventory/low_stock_alerts.html"
    context_object_name = "products"
    paginate_by = 25
    page_title = "Low Stock Alerts"
    header_icon = "warning"

    def get_queryset(self):
        """Return low-stock products, applying any active filters."""
        qs = Product.objects.low_stock().select_related("category")
        self.filterset = ProductFilterSet(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        context["total_count"] = self.filterset.qs.count()
        return context
