from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from wagtail.search import index


class TenantAwareQuerySet(models.QuerySet):
    """Custom QuerySet for tenant-aware filtering and queries.
    
    Provides convenience methods for filtering by the current tenant
    from thread-local context or other tenant-specific operations.
    """

    def filter_by_current_tenant(self):
        """Filter queryset to only include records for the current tenant.
        
        Uses ``get_current_tenant()`` from ``tenants.context`` to determine
        the active tenant. Returns an empty queryset if no tenant is currently set.
        
        Returns:
            QuerySet: Filtered to records of the current tenant, or empty if
                      no current tenant is set.
        
        Example:
            from inventory.models import Product
            
            # In a view or service layer where tenant context is set
            products = Product.objects.filter_by_current_tenant()
        """
        from tenants.context import get_current_tenant
        
        current_tenant = get_current_tenant()
        if current_tenant is None:
            return self.none()
        return self.filter(tenant=current_tenant)


class TenantAwareManager(models.Manager):
    """Custom manager providing tenant-aware query methods.
    
    Should be used as the default manager for models that inherit from
    ``TimeStampedModel`` to provide convenience methods for filtering
    by tenant context.
    """

    def get_queryset(self):
        """Return a TenantAwareQuerySet instead of a standard QuerySet."""
        return TenantAwareQuerySet(self.model, using=self._db)

    def filter_by_current_tenant(self):
        """Filter to records of the current tenant.
        
        Convenience method that delegates to the queryset's method.
        See ``TenantAwareQuerySet.filter_by_current_tenant()`` for details.
        """
        return self.get_queryset().filter_by_current_tenant()


class TimeStampedModel(index.Indexed, models.Model):
    """Audit fields inherited by all domain models.

    Provides audit timestamps, an optional ``created_by`` user link,
    and a **tenant** foreign key that scopes data to a single
    organization in a multi-tenant deployment.

    The ``tenant`` field is now **required (non-nullable)** to ensure
    all inventory data is always associated with a tenant and prevent
    orphaned records. Refer to migration 0021 for the backfill logic.

    **Tenant Consistency & Validation:**
        - The ``save()`` method validates that ``tenant`` is never None
          before persisting to the database.
        - Child models should always explicitly assign a tenant during creation.
        - Use seeders and bulk operations with caution; they should respect
          tenant context via ``seeder.execute(tenant=tenant_instance)`` or
          similar mechanisms.

    **Querying by Current Tenant:**
        - Use the default manager's `.filter_by_current_tenant()` method to
          easily filter by the tenancy context stored in thread-local storage:
        
          >>> from inventory.models import Product
          >>> from tenants.context import set_current_tenant
          >>> 
          >>> set_current_tenant(my_tenant)
          >>> products = Product.objects.filter_by_current_tenant()
    
    **Audit Field Behavior:**
        - ``created_at``: Set automatically on creation.
        - ``updated_at``: Updated automatically on each save.
        - ``created_by``: Optionally set in views/serializers to track who
          created the record. Respects tenant ownership implicitly through
          the authenticated user's tenant association.

    **Bulk Operations:**
        - Use `bulk_create()` with caution: tenant assignments must be explicit,
          and validation (``save()`` override) is bypassed. Always set `tenant`
          on each instance before bulk creating.
        - Use `bulk_update()` similarly: explicitly passing objects with tenants
          already set.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="%(app_label)s_%(class)s_set",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )

    objects = TenantAwareManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override save to validate tenant consistency.
        
        Ensures that every persisted object has a non-None tenant,
        preventing accidental creation of orphaned data.
        
        Raises:
            ValidationError: If ``self.tenant`` is None.
        
        Args:
            *args: Positional arguments passed to parent save().
            **kwargs: Keyword arguments passed to parent save().
        """
        if self.tenant_id is None:
            raise ValidationError(
                f"Cannot save {self.__class__.__name__} without a tenant. "
                "All inventory data must be scoped to a tenant."
            )
        super().save(*args, **kwargs)
