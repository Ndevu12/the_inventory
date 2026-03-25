"""Wagtail snippets for warehouse facilities and stock locations (staff / support).

Listings respect :attr:`request.tenant` from :class:`~tenants.middleware.TenantMiddleware`
(mirror :mod:`tenants.catalog_snippets`). Creating rows requires tenant context.

Tenant operators normally manage sites via the API; admin is for oversight and hierarchy review.
"""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import CreateView as SnippetCreateView
from wagtail.snippets.views.snippets import EditView as SnippetEditView
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from inventory.models import StockLocation, Warehouse
from tenants.context import get_current_tenant


def _tenant_from_request(request):
    return getattr(request, "tenant", None) or get_current_tenant()


def _restrict_warehouse_queryset(request, form):
    tenant = _tenant_from_request(request)
    if tenant is None or not hasattr(form, "fields") or "warehouse" not in form.fields:
        return
    form.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant)


class TenantInventorySnippetCreateView(SnippetCreateView):
    """Require tenant context on create and stamp ``tenant`` on new instances."""

    def dispatch(self, request, *args, **kwargs):
        if get_current_tenant() is None:
            raise PermissionDenied(
                "Tenant context is required to create inventory site snippets. "
                "For platform staff without a default tenant, add ?tenant=<slug> to the "
                "admin URL, or use the API."
            )
        return super().dispatch(request, *args, **kwargs)

    def get_initial_form_instance(self):
        instance = super().get_initial_form_instance()
        if instance is None:
            instance = self.model()
        tenant = get_current_tenant()
        if tenant is not None:
            instance.tenant = tenant
        return instance


class TenantInventorySnippetViewSet(SnippetViewSet):
    """Tenant-scoped queryset and safe create (stamped tenant)."""

    add_view_class = TenantInventorySnippetCreateView
    add_to_admin_menu = False

    def get_queryset(self, request):
        qs = self.model.objects.all().select_related("tenant")
        if issubclass(self.model, StockLocation):
            qs = qs.select_related("warehouse")
        elif self.model is Warehouse:
            pass
        tenant = getattr(request, "tenant", None)
        if tenant is not None:
            return qs.filter(tenant=tenant)
        if getattr(request, "user", None) and request.user.is_superuser:
            return qs
        return qs.none()


class WarehouseSnippetViewSet(TenantInventorySnippetViewSet):
    model = Warehouse
    icon = "home"
    menu_label = _("Warehouses")
    list_display = ["name", "is_active", "timezone_name", "tenant"]
    list_filter = ["is_active"]
    search_fields = ["name", "address", "description"]
    ordering = ["name"]


class StockLocationSnippetEditView(SnippetEditView):
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        _restrict_warehouse_queryset(self.request, form)
        return form


class StockLocationSnippetCreateView(TenantInventorySnippetCreateView):
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        _restrict_warehouse_queryset(self.request, form)
        return form


class StockLocationSnippetViewSet(TenantInventorySnippetViewSet):
    model = StockLocation
    icon = "folder-open-inverse"
    menu_label = _("Stock locations")
    add_view_class = StockLocationSnippetCreateView
    edit_view_class = StockLocationSnippetEditView
    copy_view_enabled = False
    inspect_view_enabled = True
    list_display = ["name", "warehouse", "depth", "is_active", "tenant"]
    list_filter = ["is_active", "warehouse"]
    search_fields = ["name", "description"]
    ordering = ["path"]


class InventorySitesSnippetViewSetGroup(SnippetViewSetGroup):
    items = [
        WarehouseSnippetViewSet,
        StockLocationSnippetViewSet,
    ]
    menu_label = _("Warehouses & locations")
    menu_icon = "site"
    menu_name = "inventory-sites"
    menu_order = 145


register_snippet(InventorySitesSnippetViewSetGroup)
