"""Tenant-scoped managers.

``TenantAwareManager`` is the default manager pattern for tenant-scoped
models. It filters querysets by the current tenant stored in thread-local
context so application code does not accidentally mix tenants.

**Which API to use**

- **Ordinary queries** (``objects.all()``, ``.filter()``, …): Go through
  ``get_queryset()``. When context has a tenant, results are scoped to it.
  When context has no tenant, the queryset is **unfiltered** and a warning is
  logged — that path is for migrations, shell, and management commands, not
  typical request handling.

- **``for_tenant(tenant)``** (manager): Returns rows for the given tenant
  **regardless** of thread-local context. Use when the tenant is passed in
  explicitly (services, tasks) instead of relying on ``set_current_tenant``.

- **``unscoped()``** (manager): No tenant filter — all rows. Use only for
  migrations, data fixes, and management commands that must see every tenant.

The queryset class also provides **``for_tenant(tenant)``** on an existing
queryset (e.g. after ``unscoped()``) to narrow by tenant.
"""

import logging

from django.db import models

from tenants.context import get_current_tenant

logger = logging.getLogger(__name__)


class TenantAwareQuerySet(models.QuerySet):
    """QuerySet used by ``TenantAwareManager``."""

    def for_tenant(self, tenant):
        """Return rows where ``tenant`` matches the given instance or PK."""
        return self.filter(tenant=tenant)


class TenantAwareManager(models.Manager):
    """Manager that scopes default queries to the current tenant from context.

    If ``get_current_tenant()`` is set, ``get_queryset()`` filters to that
    tenant. If it is ``None``, the queryset is not filtered and a warning is
    emitted so accidental use in request paths is visible in logs.
    """

    def get_queryset(self):
        qs = TenantAwareQuerySet(self.model, using=self._db)
        tenant = get_current_tenant()
        if tenant is not None:
            qs = qs.filter(tenant=tenant)
        else:
            logger.warning("Querying without tenant context")
        return qs

    def for_tenant(self, tenant):
        """Explicit tenant scope; does not use thread-local context for filtering.

        Prefer this in code that receives ``tenant`` as an argument so queries
        stay correct even if context was not set.
        """
        return self.unscoped().filter(tenant=tenant)

    def unscoped(self):
        """All rows for this model, every tenant — no automatic filter.

        For migrations, management commands, and other cross-tenant work only.
        """
        return TenantAwareQuerySet(self.model, using=self._db)
