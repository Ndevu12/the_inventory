"""Wagtail Snippet support for tenant management.

Provides:
- ``TenantSnippetViewSet`` — platform-level CRUD for tenants in the
  Wagtail admin sidebar.
- ``TenantScopedSnippetViewSet`` — base class for viewsets that
  automatically filter by the current tenant (for future use).
"""

from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from tenants.context import get_current_tenant
from tenants.models import Tenant


class TenantSnippetViewSet(SnippetViewSet):
    """Platform-level tenant management in the Wagtail admin."""

    model = Tenant
    icon = "group"
    menu_label = "Tenants"
    menu_order = 100
    add_to_admin_menu = True
    list_display = [
        "name",
        "slug",
        "subscription_plan",
        "subscription_status",
        "is_active",
    ]
    list_filter = ["is_active", "subscription_plan", "subscription_status"]
    search_fields = ["name", "slug"]


register_snippet(TenantSnippetViewSet)


class TenantScopedSnippetViewSet(SnippetViewSet):
    """SnippetViewSet that automatically scopes queries to the current tenant.

    Usage::

        from tenants.snippets import TenantScopedSnippetViewSet

        class ProductSnippetViewSet(TenantScopedSnippetViewSet):
            model = Product
            # ... panels, etc.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant is not None and hasattr(qs.model, "tenant"):
            qs = qs.filter(tenant=tenant)
        return qs
