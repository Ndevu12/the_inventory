"""Wagtail snippets for translatable catalog models (staff / support).

Registers Product, Category, Supplier, and Customer so they appear in the admin and
work with ``wagtail-localize`` (listing **Translate** / **Sync translated snippets**
when the user has ``wagtail_localize.submit_translation``).

Listings are scoped to :attr:`request.tenant` from :class:`~tenants.middleware.TenantMiddleware`.
Platform superusers without a tenant membership see all rows; everyone else needs tenant
context. **Creating** snippets requires tenant context — platform staff can add
``?tenant=<slug>`` to the admin URL.

Tenant operators normally author catalog data via the REST API; this module is optional
support and translation tooling in `/admin/`.
"""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import CreateView as SnippetCreateView
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from inventory.models import Category, Product
from procurement.models import Supplier
from sales.models import Customer

from tenants.context import get_current_tenant


class TenantCatalogSnippetCreateView(SnippetCreateView):
    """Require tenant context on create and stamp new rows with ``request`` tenant."""

    def dispatch(self, request, *args, **kwargs):
        if get_current_tenant() is None:
            raise PermissionDenied(
                "Tenant context is required to create catalog snippets. "
                "For platform staff without a default tenant, add ?tenant=<slug> to the "
                "admin URL, or create catalog rows via the API."
            )
        return super().dispatch(request, *args, **kwargs)

    def get_initial_form_instance(self):
        instance = super().get_initial_form_instance()
        if instance is not None:
            tenant = get_current_tenant()
            if tenant is not None:
                instance.tenant = tenant
        return instance


class TenantCatalogSnippetViewSet(SnippetViewSet):
    """Snippet viewset with tenant-scoped queryset and safe create semantics."""

    add_view_class = TenantCatalogSnippetCreateView
    add_to_admin_menu = False

    def get_queryset(self, request):
        qs = self.model.objects.all().select_related("tenant", "locale")
        tenant = getattr(request, "tenant", None)
        if tenant is not None:
            return qs.filter(tenant=tenant)
        if getattr(request, "user", None) and request.user.is_superuser:
            return qs
        return qs.none()


class ProductCatalogSnippetViewSet(TenantCatalogSnippetViewSet):
    model = Product
    icon = "box"
    menu_label = _("Products")
    list_display = ["sku", "name", "locale", "is_active", "tenant"]
    list_filter = ["locale", "is_active"]
    search_fields = ["sku", "name"]
    ordering = ["sku"]


class CategoryCatalogSnippetViewSet(TenantCatalogSnippetViewSet):
    model = Category
    icon = "folder-open-inverse"
    menu_label = _("Categories")
    list_display = ["name", "slug", "locale", "is_active", "tenant"]
    list_filter = ["locale", "is_active"]
    search_fields = ["name", "slug"]
    ordering = ["name"]


class SupplierCatalogSnippetViewSet(TenantCatalogSnippetViewSet):
    model = Supplier
    icon = "user"
    menu_label = _("Suppliers")
    list_display = ["code", "name", "locale", "is_active", "tenant"]
    list_filter = ["locale", "is_active"]
    search_fields = ["code", "name", "contact_name"]
    ordering = ["name"]


class CustomerCatalogSnippetViewSet(TenantCatalogSnippetViewSet):
    model = Customer
    icon = "order"
    menu_label = _("Customers")
    list_display = ["code", "name", "locale", "is_active", "tenant"]
    list_filter = ["locale", "is_active"]
    search_fields = ["code", "name", "contact_name"]
    ordering = ["name"]


class CatalogSnippetViewSetGroup(SnippetViewSetGroup):
    items = [
        ProductCatalogSnippetViewSet,
        CategoryCatalogSnippetViewSet,
        SupplierCatalogSnippetViewSet,
        CustomerCatalogSnippetViewSet,
    ]
    menu_label = _("Catalog (translations)")
    menu_icon = "site"
    menu_name = "catalog-translations"
    menu_order = 150


register_snippet(CatalogSnippetViewSetGroup)
