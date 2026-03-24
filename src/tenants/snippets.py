"""Wagtail Snippet support for tenant management.

Provides:
- ``TenantSnippetViewSet`` — platform-level CRUD for tenants in the
  Wagtail admin sidebar.
- ``TenantScopedSnippetViewSet`` — base class for viewsets that
  automatically filter by the current tenant (for future use).
"""

from django.urls import path

from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from tenants.context import get_current_tenant
from tenants.models import Tenant
from tenants.wagtail_views import (
    TenantCreateView,
    TenantDeactivateView,
    TenantEditView,
    TenantReactivateView,
)


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
        "usage_summary",
    ]
    list_filter = ["is_active", "subscription_plan", "subscription_status"]
    search_fields = ["name", "slug"]
    add_view_class = TenantCreateView
    edit_view_class = TenantEditView

    def get_urlpatterns(self):
        conv = self.pk_path_converter
        patterns = super().get_urlpatterns()
        patterns.extend([
            path(
                f"deactivate/<{conv}:pk>/",
                TenantDeactivateView.as_view(),
                name="deactivate",
            ),
            path(
                f"reactivate/<{conv}:pk>/",
                TenantReactivateView.as_view(),
                name="reactivate",
            ),
        ])
        return patterns


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
