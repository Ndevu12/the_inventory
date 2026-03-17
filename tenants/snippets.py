"""Tenant-scoped Wagtail Snippet support.

Provides a mixin for SnippetViewSet that automatically filters
querysets by the current tenant set in the middleware.  Snippets
created through these viewsets also get the tenant assigned.
"""

from wagtail.snippets.views.snippets import SnippetViewSet

from tenants.context import get_current_tenant


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
