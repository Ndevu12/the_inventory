"""Inventory views for the Wagtail admin.

All views follow the project's OOP standard — class-based with
WagtailAdminTemplateMixin for consistent admin chrome.
"""

from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, TemplateView
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from wagtail.search.backends import get_search_backend

from inventory.filters import ProductFilterSet
from inventory.models import Category, Product, StockLocation
from tenants.context import get_current_tenant
from tenants.permissions import get_membership


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

    def _get_current_tenant(self):
        """Get current tenant and raise PermissionDenied if not set or user lacks access."""
        tenant = get_current_tenant()
        if not tenant:
            raise PermissionDenied("Tenant context is not set.")
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        if not get_membership(self.request.user, tenant):
            raise PermissionDenied("You do not have access to this tenant.")
        return tenant

    def get_queryset(self):
        """Return low-stock products, applying any active filters."""
        tenant = self._get_current_tenant()
        qs = (
            Product.objects.filter(tenant=tenant)
            .low_stock()
            .select_related("category")
            .order_by("sku")
        )
        self.filterset = ProductFilterSet(
            self.request.GET, queryset=qs, tenant=tenant
        )
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        context["total_count"] = self.filterset.qs.count()
        return context


class InventorySearchView(WagtailAdminTemplateMixin, TemplateView):
    """Unified search across all inventory models (admin-only).

    Searches Products, Categories, and StockLocations using the Wagtail
    search backend.  Only active items are returned.  Results are grouped
    by model type for clarity.
    """

    template_name = "inventory/search.html"
    page_title = "Inventory Search"
    header_icon = "search"

    def _get_current_tenant(self):
        """Get current tenant and raise PermissionDenied if not set or user lacks access."""
        tenant = get_current_tenant()
        if not tenant:
            raise PermissionDenied("Tenant context is not set.")
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        if not get_membership(self.request.user, tenant):
            raise PermissionDenied("You do not have access to this tenant.")
        return tenant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self._get_current_tenant()
        query = self.request.GET.get("q", "").strip()
        context["search_query"] = query

        if query:
            backend = get_search_backend()
            context["product_results"] = backend.search(
                query,
                Product.objects.filter(tenant=tenant, is_active=True),
            )
            context["category_results"] = backend.search(
                query,
                Category.objects.filter(tenant=tenant, is_active=True),
            )
            context["location_results"] = backend.search(
                query,
                StockLocation.objects.filter(tenant=tenant, is_active=True),
            )
        else:
            context["product_results"] = Product.objects.none()
            context["category_results"] = Category.objects.none()
            context["location_results"] = StockLocation.objects.none()

        return context
