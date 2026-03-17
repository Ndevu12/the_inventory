"""Tenant-scoped managers.

``TenantAwareManager`` is the default manager for every model that
inherits from ``TimeStampedModel``.  It transparently filters querysets
by the current tenant stored in thread-local context, so application
code never accidentally leaks data across tenants.

An ``unscoped()`` escape hatch is provided for cross-tenant operations
such as migrations and management commands.
"""

from django.db import models

from tenants.context import get_current_tenant


class TenantAwareQuerySet(models.QuerySet):
    """QuerySet that can be filtered to a specific tenant."""

    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)


class TenantAwareManager(models.Manager):
    """Auto-scoping manager.

    When a tenant is set in thread-local context, all queries are
    automatically filtered to that tenant.  When no tenant is set (e.g.,
    management commands, migrations, shell), the queryset is unfiltered.
    """

    def get_queryset(self):
        qs = TenantAwareQuerySet(self.model, using=self._db)
        tenant = get_current_tenant()
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        return qs

    def unscoped(self):
        """Bypass tenant filtering — use with caution."""
        return TenantAwareQuerySet(self.model, using=self._db)
